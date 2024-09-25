# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ecommerce_id = fields.Integer(string="Ecommerce ID")
    ecommerce_shipping_id = fields.Integer(string="Ecommerce Shipping ID")

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if self.ecommerce_id:
            res["ecommerce_id"] = self.ecommerce_id
        if self.ecommerce_shipping_id:
            res["ecommerce_shipping_id"] = self.ecommerce_shipping_id
        return res
