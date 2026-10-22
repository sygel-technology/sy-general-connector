# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class EcommerceConnector(models.Model):
    _inherit = "ecommerce.connector"

    def _get_new_partner_vals(self, values, ecommerce_connection):
        vals = super()._get_new_partner_vals(values, ecommerce_connection)
        vals["fiscal_position_type"] = (
            "b2c" if values.get("customer").get("typeClient") == "individual" else "b2b"
        )
        return vals

    def _get_fiscal_position_domain(self, delivery_address, company):
        domain = super()._get_fiscal_position_domain(delivery_address, company)
        domain.append(("fiscal_position_type", "=", "b2c"))
        return domain
