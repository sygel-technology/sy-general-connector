# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EcommercePartner(models.Model):
    _name = "ecommerce.partner"
    _description = "Ecommerce Partner"

    partner_id = fields.Many2one(
        string="Partner", comodel_name="res.partner", required=True
    )
    ecommerce_connection_id = fields.Many2one(
        string="Ecommerce", comodel_name="ecommerce.connection", required=True
    )
    ecommerce_id = fields.Integer(string="Ecommerce ID", required=True)

    _sql_constraints = [
        (
            "product_product_ecommerce_connection_unique",
            "unique(partner_id, ecommerce_connection_id)",
            "Only one partner entry in an ecommerce.",
        )
    ]
