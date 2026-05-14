# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models, api
from odoo.exceptions import UserError


# =========================
# MRP PRODUCTION
# =========================
class MrpProduction(models.Model):
    """Inherited module 'mrp.production' and added required fields"""
    _inherit = 'mrp.production'

    source = fields.Char(
        string='Source of Order',
        help='Sale Order from which this Manufacturing Order was created.',
    )
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Line',
        help="Corresponding sale order line id",
    )
    qty_to_produce = fields.Float(
        string='Quantity to Produce',
        help='The number of products to be produced.',
    )
    customer_ref = fields.Char(
        string="Customer ID",
        help="Customer reference carried from the sale order.",
    )

    def action_confirm(self):
        for mo in self:
            if mo.sale_line_id and mo.sale_line_id.bom_id:
                correct_bom = mo.sale_line_id.bom_id

                if mo.bom_id != correct_bom:
                    mo.bom_id = correct_bom.id

                    mo.move_raw_ids.filtered(
                        lambda m: m.state not in ('done', 'cancel')
                    ).unlink()

                    # ✅ FORCE recompute safely
                    mo._compute_move_raw_ids()

        res = super().action_confirm()

        for mo in self:
            mo._update_move_destinations()

        return res


    def _update_move_destinations(self):
        for mo in self:
            for move in mo.move_raw_ids:
                if move.state in ['done', 'cancel']:
                    continue
                product_location = move.product_id.property_stock_production
                if product_location:
                    move.location_dest_id = product_location.id
                else:
                    move.location_dest_id = mo.location_src_id

    # ------------------------------------------------------------------
    # Called by the Shop Floor OWL "Print Barcode" button.
    # Shop Floor fires actions on mrp.production, not mrp.workorder,
    # so this method must exist here and forward to the right work order.
    # ------------------------------------------------------------------
    def action_open_barcode_controller(self):
        self.ensure_one()

        # Pick the first work order that has a barcode serial computed
        wo = self.workorder_ids.sorted('sequence').filtered(
            lambda w: w.wo_barcode_serial
        )[:1]

        # Fallback: just take the first work order
        if not wo:
            wo = self.workorder_ids.sorted('sequence')[:1]

        if not wo:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Work Order',
                    'message': 'No work orders found on this Manufacturing Order.',
                    'type': 'warning',
                    'sticky': False,
                },
            }

        return {
            'type': 'ir.actions.act_url',
            'url': f'/wo-barcode/{wo.id}',
            'target': 'new',
        }

    # backward compatibility
    def action_print_semi_barcode(self):
        return self.action_open_barcode_controller()


# =========================
# MRP WORKORDER
# (button_start validation — kept here from original file,
#  full workorder logic lives in mrp_workorder.py)
# =========================
class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

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
            MrpWorkorder,
            self.with_context(skip_consumption=True)
        ).button_start()


# =========================
# WORK CENTER
# =========================
class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    location_id = fields.Many2one(
        'stock.location',
        string='Production Location',
        help="Default source location used for component moves in work orders.",
    )


# =========================
# STOCK MOVE
# =========================
class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.raw_material_production_id and move.operation_id:
                workcenter = move.operation_id.workcenter_id
                if workcenter.location_id:
                    move.location_id = workcenter.location_id.id
        return moves