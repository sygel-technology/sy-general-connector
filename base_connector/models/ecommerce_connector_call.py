# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EcommerConnectorCall(models.Model):
    _name = "ecommerce.connector.call"
    _description = "Ecommerce Connector Call"
    _order = "datetime DESC"

    name = fields.Char()
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done"), ("error", "Error")],
        readonly=True,
        default="draft",
    )
    ecommerce_origin = fields.Char()
    ecommerce_connection_id = fields.Many2one(
        string="Ecommerce Connection",
        comodel_name="ecommerce.connection",
        readonly=True,
    )
    datetime = fields.Datetime(string="Date", readonly=True)
    message_in = fields.Text(readonly=True)
    message_out = fields.Text(readonly=True)
    error = fields.Text(readonly=True)
    # TODO: Añadir ambito o operacion. Que sea compatible con la operacion del otro modulo

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "ecommerce.connector.call"
            )
        return super().create(vals_list)
