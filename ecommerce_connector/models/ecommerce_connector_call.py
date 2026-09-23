# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EcommerConnectorCall(models.Model):
    _inherit = "ecommerce.connector.call"

    sale_order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order", readonly=True
    )
    account_move_id = fields.Many2one(
        comodel_name="account.move", string="Invoice", readonly=True
    )
    operation = fields.Selection(
        [
            ("invoice", "Invoice"),
            ("credit", "Credit Note"),
            ("update_contact", "Update Contact"),
        ],
        readonly=True,
    )
