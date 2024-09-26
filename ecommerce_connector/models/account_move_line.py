# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    ecommerce_id = fields.Integer(string="Ecommerce ID")
    ecommerce_shipping_id = fields.Integer(string="Ecommerce Shipping ID")
