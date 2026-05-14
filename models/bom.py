from odoo import models, fields, api

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    source_bom_id = fields.Many2one(
        'mrp.bom',
        string="Reference BoM"
    )

    @api.onchange('source_bom_id')
    def _onchange_source_bom_id(self):
        if not self.source_bom_id:
            return

        source_ops = list(self.source_bom_id.operation_ids)

        # Copy operations (creates new routing records for the new BoM)
        operations = []
        for op in source_ops:
            operations.append((0, 0, {
                'name': op.name,
                'workcenter_id': op.workcenter_id.id,
                'time_cycle_manual': op.time_cycle_manual,
                'sequence': op.sequence,
            }))
        self.operation_ids = [(5, 0, 0)] + operations

        # Copy components — point operation_id directly to the SOURCE BoM's
        # real mrp.routing.workcenter record ID. These records already exist
        # in the DB so Odoo can resolve and display them in the onchange.
        # The domain on operation_id restricts to allowed_operation_ids of the
        # parent BoM — after Save the new BoM will have its own copied ops,
        # so the save handler below re-links them by name match.
        lines = []
        for line in self.source_bom_id.bom_line_ids:
            vals = {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom_id': line.product_uom_id.id,
            }
            if line.operation_id:
                vals['operation_id'] = line.operation_id.id
            lines.append((0, 0, vals))

        self.bom_line_ids = [(5, 0, 0)] + lines

    def write(self, vals):
        res = super().write(vals)
        # After save: if this BoM was created from a source_bom_id,
        # re-link each component's operation_id to the BoM's OWN new
        # operations (matched by name), so domain constraints are satisfied.
        for bom in self:
            if not bom.source_bom_id:
                continue
            # Build name → new op record map
            op_by_name = {op.name: op for op in bom.operation_ids}
            for line in bom.bom_line_ids:
                if line.operation_id and line.operation_id not in bom.operation_ids:
                    matched = op_by_name.get(line.operation_id.name)
                    if matched:
                        line.operation_id = matched.id
        return res