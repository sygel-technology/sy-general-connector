# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ecommerce_product_template_ids = fields.One2many(
        string="Ecommerce Product Template",
        comodel_name="ecommerce.product.template",
        inverse_name="product_template_id",
    )
