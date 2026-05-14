# -*- coding: utf-8 -*-
from odoo import models, fields, api


# =========================
# PARTNER
# =========================
class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_ref = fields.Char(
        string="Customer ID",
        copy=False,
        readonly=True
    )

    # ✅ keep this (works fine despite warning)
    _sql_constraints = [
        ('customer_ref_unique', 'unique(customer_ref)', 'Customer ID must be unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('customer_ref'):
                vals['customer_ref'] = self.env['ir.sequence'].next_by_code('customer.ref')
        return super().create(vals_list)


# =========================
# SALE ORDER
# =========================
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_ref = fields.Char(
        related='partner_id.customer_ref',
        string="Customer ID",
        store=True,
        readonly=True
    )


# =========================
# MRP PRODUCTION (SAFE)
# =========================
class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    customer_ref = fields.Char(
        string="Customer ID",
        compute="_compute_customer_ref",
        store=True,
        readonly=True
    )

    @api.depends('origin')
    def _compute_customer_ref(self):
        for rec in self:
            customer_ref = False

            if rec.origin:
                origin_clean = rec.origin.split(',')[0].strip()

                sale = self.env['sale.order'].search(
                    [('name', '=', origin_clean)],
                    limit=1
                )

                if sale and sale.partner_id:
                    customer_ref = sale.partner_id.customer_ref

            rec.customer_ref = customer_ref