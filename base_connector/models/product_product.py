# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    ecommerce_product_ids = fields.One2many(
        string="Ecommerce Product",
        comodel_name="ecommerce.product.product",
        inverse_name="product_id",
    )
