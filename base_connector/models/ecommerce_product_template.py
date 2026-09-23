# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EcommerceProductTemplate(models.Model):
    _name = "ecommerce.product.template"
    _description = "Ecommerce Product Template"

    product_template_id = fields.Many2one(
        string="Product Template", comodel_name="product.template", required=True
    )
    ecommerce_connection_id = fields.Many2one(
        string="Ecommerce", comodel_name="ecommerce.connection", required=True
    )
    ecommerce_id = fields.Integer(string="Ecommerce ID", required=True)

    _sql_constraints = [
        (
            "product_template_ecommerce_connection_unique",
            "unique(product_template_id, ecommerce_connection_id)",
            "Only one product entry in an ecommerce.",
        )
    ]
