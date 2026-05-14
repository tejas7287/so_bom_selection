from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_manufacture(self, procurements):
        res = super()._run_manufacture(procurements)

        for procurement, rule in procurements:
            values = procurement.values

            bom_val = values.get('bom_id')
            sale_line_id = values.get('sale_line_id')

            if not (bom_val and sale_line_id):
                continue

            # Ensure BOM record
            bom = bom_val if not isinstance(bom_val, int) else self.env['mrp.bom'].browse(bom_val)

            # Find MO
            mo = self.env['mrp.production'].search([
                ('origin', '=', procurement.origin),
                ('product_id', '=', procurement.product_id.id),
            ], limit=1)

            if not mo:
                continue

            # Apply BOM + sale line
            mo.write({
                'bom_id': bom.id,
                'sale_line_id': sale_line_id.id if hasattr(sale_line_id, 'id') else sale_line_id,
            })

            # Remove old components (clean state)
            mo.move_raw_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
            ).unlink()

            # ❌ DO NOT call _action_confirm here

        return res