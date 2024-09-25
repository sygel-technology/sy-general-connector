# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    ecommerce_id = fields.Integer(string="Ecommerce ID")
    ecommerce_connector_id = fields.Many2one(
        string="Ecommerce Connection", comodel_name="ecommerce.connection"
    )
