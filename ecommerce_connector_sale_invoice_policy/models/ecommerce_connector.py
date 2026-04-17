# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class EcommerceConnector(models.Model):
    _inherit = "ecommerce.connector"

    def _get_additional_order_vals(self, values, ecommerce_connection):
        vals = super()._get_additional_order_vals(values, ecommerce_connection)
        if ecommerce_connection.invoice_policy:
            vals["invoice_policy"] = ecommerce_connection.invoice_policy
        return vals
