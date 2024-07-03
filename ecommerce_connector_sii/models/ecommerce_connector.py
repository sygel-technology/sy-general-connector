# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class EcommerceConnector(models.Model):
    _inherit = "ecommerce.connector"

    def _get_new_partner_vals(self, values, ecommerce_connection):
        vals = super()._get_new_partner_vals(values, ecommerce_connection)
        vals["sii_simplified_invoice"] = True if not values.get(
            'customer'
        ).get('vat') else False
        return vals
