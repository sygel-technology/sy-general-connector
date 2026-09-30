# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EcommerceProductProduct(models.Model):
    _name = "ecommerce.product.product"
    _description = "Ecommerce Product Product"

    product_id = fields.Many2one(
        string="Product", comodel_name="product.product", required=True
    )
    ecommerce_connection_id = fields.Many2one(
        string="Ecommerce", comodel_name="ecommerce.connection", required=True
    )
    ecommerce_id = fields.Integer(string="Ecommerce ID", required=True)

    _sql_constraints = [
        (
            "product_product_ecommerce_connection_unique",
            "unique(product_id, ecommerce_connection_id)",
            "Only one product entry in an ecommerce.",
        )
    ]
