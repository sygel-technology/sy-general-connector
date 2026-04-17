# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EcommerceConnection(models.Model):
    _inherit = "ecommerce.connection"

    invoice_policy = fields.Selection(
        [
            ("product", "Products Invoice Policy"),
            ("order", "Ordered quantities"),
            ("delivery", "Delivered quantities"),
        ],
    )
