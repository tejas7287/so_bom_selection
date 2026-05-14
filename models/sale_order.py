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
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    reference_template_id = fields.Many2one(
        'mrp.bom',
        string="Reference Template",
        domain=[('type', '=', 'normal')]
    )
    def action_open_bom_overview(self):
        """Open BoM Overview for the BOM selected on the first SO line that has one."""
        self.ensure_one()
        bom = None
        for line in self.order_line:
            if line.bom_id:
                bom = line.bom_id
                break

        if not bom:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Bill of Material',
                    'message': 'Please select a Bill of Material on the order line first.',
                    'type': 'warning',
                    'sticky': False,
                },
            }

        action = self.env['ir.actions.act_window']._for_xml_id('mrp.mrp_bom_form_action')
        action.update({
            'res_id': bom.id,
            'views': [(False, 'form')],
            'target': 'current',
            'context': {'active_id': bom.id},
        })
        return action

    def action_confirm(self):
        res = super().action_confirm()

        for order in self:
            if not order.reference_template_id:
                continue

            mos = self.env['mrp.production'].search([
                ('origin', '=', order.name),
                ('state', 'in', ['confirmed', 'planned'])
            ])

            for mo in mos:
                # 🔥 DO NOT TOUCH bom_id → components must come from line BOM

                # Get operations from Reference Template
                template_ops = order.reference_template_id.operation_ids

                if template_ops:
                    # Remove existing work orders
                    mo.workorder_ids.unlink()

                    workorders_vals = []
                    for op in template_ops:
                        workorders_vals.append((0, 0, {
                            'name': op.name,
                            'workcenter_id': op.workcenter_id.id,
                            'duration_expected': op.time_cycle_manual,
                        }))

                    mo.write({
                        'workorder_ids': workorders_vals
                    })

                # Sync quantity
                mo.qty_to_produce = mo.product_qty

        return res