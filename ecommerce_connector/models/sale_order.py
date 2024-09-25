# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ecommerce_id = fields.Integer(string="Ecommerce ID")
    ecommerce_connector_id = fields.Many2one(
        string="Ecommerce Connection", comodel_name="ecommerce.connection"
    )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.ecommerce_connector_id:
            vals["ecommerce_connector_id"] = self.ecommerce_connector_id.id
        return vals
