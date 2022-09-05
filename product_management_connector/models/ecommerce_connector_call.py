# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EcommerConnectorCall(models.Model):
    _inherit = "ecommerce.connector.call"

    operation = fields.Selection(selection_add=[
        ('create_product', 'Create Product'),
        ('update_product', 'Update Product')
    ])
