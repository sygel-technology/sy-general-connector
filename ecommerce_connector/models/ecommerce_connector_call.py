# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class EcommerConnectorCall(models.Model):
    _name = "ecommerce.connector.call"
    _description = "Ecommerce Connector Call"
    _order = "datetime DESC"

    name = fields.Char(
        string="Name"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done"), ("error", "Error")],
        string="State",
        readonly=True,
        default="draft"
    )
    ecommerce_origin = fields.Char(
        string="Ecommerce Origin"
    )
    ecommerce_connection_id = fields.Many2one(
        string="Ecommerce Connection",
        comodel_name="ecommerce.connection",
        readonly=True
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        readonly=True
    )
    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        readonly=True
    )
    datetime = fields.Datetime(
        string="Date",
        readonly=True
    )
    message_in = fields.Text(
        string="Message In",
        readonly=True
    )
    message_out = fields.Text(
        string="Message Out",
        readonly=True
    )
    error = fields.Text(
        string="Error",
        readonly=True
    )
    operation = fields.Selection(
        [("invoice", "Invoice"), ("credit", "Credit Note")],
        string="Operation",
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "ecommerce.connector.call"
            )
        return super().create(vals_list)
