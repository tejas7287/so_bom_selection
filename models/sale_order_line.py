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
from odoo import fields, models


class SaleOrderLine(models.Model):
    """Inherited model 'sale.order.line' and added required fields"""
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one(
        'mrp.bom',
        string='Bill of Material',
        help="Bill of materials for the product"
    )

    product_template_id = fields.Many2one(
        related="product_id.product_tmpl_id",
        string="Template Id of Selected Product",
        help="Template id of the selected product"
    )

    # 🔥 FORCE correct BOM (orange BOM) into MO
    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()

        # ✅ MUST PASS RECORD (NOT ID)
        if self.bom_id:
            res['bom_id'] = self.bom_id

        # 🔥 also keep linkage
        res['sale_line_id'] = self.id

        return res

    # 🔗 Link MO to stock move
    def _action_launch_stock_rule(self):
        result = super()._action_launch_stock_rule()

        for rec in self:
            mo = self.env['mrp.production'].search(
                [('sale_line_id', '=', rec.id)],
                limit=1
            )

            if not mo:
                continue

            move = self.env['stock.move'].search(
                [('sale_line_id', '=', rec.id)],
                limit=1
            )

            if move and not move.created_production_id:
                move.created_production_id = mo.id

        return result