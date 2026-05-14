# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import UserError


def _no_lot_warning():
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'No Barcode Available',
            'message': 'No semi-finished lot found. Please finish the work order first.',
            'type': 'warning',
            'sticky': False,
        },
    }


def _clean(text):
    """Strip non-alphanumeric chars (keep hyphens) for use in lot/barcode names."""
    return re.sub(r'[^A-Za-z0-9\-]', '-', text or '').strip('-')


# =========================
# MRP WORKORDER
# =========================
class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
    )
    wc_cost_hour = fields.Float(
        string="WC Cost/hr",
        related='workcenter_id.costs_hour',
        store=True,
    )
    employee_cost_hour = fields.Monetary(
        string="Emp Cost/hr",
        related='workcenter_id.employee_costs_hour',
        currency_field='currency_id',
        store=True,
    )
    semi_finished_product_ids = fields.Many2many(
        'product.product',
        related='workcenter_id.semi_finished_product_ids',
        readonly=True,
    )
    customer_ref = fields.Char(
        string="Customer ID",
        related='production_id.customer_ref',
        store=True,
        readonly=True,
    )
    semi_finished_lot_id = fields.Many2one(
        'stock.lot',
        string="Semi-Finished Serial",
        readonly=True,
        copy=False,
    )

    # -------------------------------------------------------
    # Computed barcode serial:  <WORKCENTER>-<MO>
    # e.g.  WELDING-WH-MO-00042
    # -------------------------------------------------------
    wo_barcode_serial = fields.Char(
        string="WO Barcode Serial",
        compute='_compute_wo_barcode_serial',
        store=True,
    )

    @api.depends('workcenter_id.name', 'production_id.name')
    def _compute_wo_barcode_serial(self):
        for wo in self:
            wc = _clean(wo.workcenter_id.name or 'WC').upper()
            mo = _clean(wo.production_id.name or 'MO').upper()
            wo.wo_barcode_serial = f"{wc}-{mo}"

    # -------------------------
    # START: validate component reservation
    # -------------------------
    def button_start(self):
        for wo in self:
            workcenter = wo.workcenter_id
            production = wo.production_id
            capacity_lines = workcenter.capacity_ids
            raw_moves = production.move_raw_ids
            missing_products = []

            for line in capacity_lines:
                product = line.product_id
                required_qty = line.capacity or 0.0

                moves = raw_moves.filtered(
                    lambda m: m.product_id.id == product.id
                    and m.state not in ['done', 'cancel']
                )
                if not moves:
                    missing_products.append(
                        f"{product.display_name} (No component in MO)"
                    )
                    continue

                reserved_qty = sum(
                    sum(m.move_line_ids.mapped('quantity'))
                    for m in moves
                )
                if reserved_qty < required_qty:
                    missing_products.append(
                        f"{product.display_name} "
                        f"(Needed: {required_qty}, Reserved: {reserved_qty})"
                    )

            if missing_products:
                raise UserError(
                    "Cannot start Work Order.\n\n"
                    "Required components not reserved:\n\n"
                    + "\n".join(missing_products)
                )

        return super(
            MrpWorkOrder, self.with_context(skip_consumption=True)
        ).button_start()

    # -------------------------
    # FINISH: generate semi-finished lot + stock move
    # Lot name = wo_barcode_serial so lot ↔ barcode are 1-to-1
    # -------------------------
    def button_finish(self):
        res = super().button_finish()

        for wo in self:
            if not wo.semi_finished_product_ids:
                continue

            production_location = self.env['stock.location'].search([
                ('usage', '=', 'production'),
                ('company_id', 'in', [wo.company_id.id, False]),
            ], limit=1)

            dest_location = wo.production_id.location_dest_id
            # Lot name = unique per work order:  <WC>-<MO>
            lot_name = wo.wo_barcode_serial

            for product in wo.semi_finished_product_ids:
                lot = self.env['stock.lot'].search([
                    ('name', '=', lot_name),
                    ('product_id', '=', product.id),
                ], limit=1)

                if not lot:
                    lot = self.env['stock.lot'].sudo().create({
                        'name': lot_name,
                        'product_id': product.id,
                        'company_id': wo.company_id.id,
                    })

                wo.semi_finished_lot_id = lot.id

                self.env['stock.move'].sudo().create({
                    'reference': f'Semi-finished: {product.name}',
                    'product_id': product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': product.uom_id.id,
                    'location_id': production_location.id,
                    'location_dest_id': dest_location.id,
                    'company_id': wo.company_id.id,
                    'origin': wo.production_id.name,
                    'state': 'done',
                    'move_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'product_uom_id': product.uom_id.id,
                        'quantity': 1.0,
                        'lot_id': lot.id,
                        'location_id': production_location.id,
                        'location_dest_id': dest_location.id,
                        'company_id': wo.company_id.id,
                        'state': 'done',
                    })],
                })

        return res

    # -------------------------
    # OPEN LOT FORM (backend link)
    # -------------------------
    def action_open_semi_barcode(self):
        self.ensure_one()
        if not self.semi_finished_lot_id:
            return {}
        return {
            'type': 'ir.actions.act_url',
            'url': (
                f'/web#id={self.semi_finished_lot_id.id}'
                f'&model=stock.lot&view_type=form'
            ),
            'target': 'new',
        }

    # -------------------------
    # PRINT BARCODE — opens /wo-barcode/<id> in a new tab
    # Works from backend form AND Shop Floor OWL button
    # -------------------------
    def action_open_barcode_controller(self):
        """Open the per-work-order barcode print page."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/wo-barcode/{self.id}',
            'target': 'new',
        }

    # backward compatibility
    def action_print_semi_barcode(self):
        return self.action_open_barcode_controller()

    def button_start(self, bypass=False):
        return super().button_start()


# =========================
# WORK CENTER
# =========================
class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    semi_finished_product_ids = fields.Many2many(
        'product.product',
        string="Semi Finished Goods",
        domain="[('product_tmpl_id.is_semi_finished', '=', True)]",
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Production Location',
        help="Default source location used for component moves in work orders.",
    )


# =========================
# PRODUCT TEMPLATE
# =========================
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_semi_finished = fields.Boolean(
        string="Semi Finished Good",
    )


# =========================
# STOCK LOT
# =========================
class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_print_barcode(self):
        """Open the barcode print page for this lot (generic lot path)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/barcode/{self.name}',
            'target': 'new',
        }
