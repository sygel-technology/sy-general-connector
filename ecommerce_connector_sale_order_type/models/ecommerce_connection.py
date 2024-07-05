# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EcommerceConnection(models.Model):
    _inherit = "ecommerce.connection"

    sale_order_type_id = fields.Many2one(
        comodel_name="sale.order.type", name="Sale Order Type"
    )
