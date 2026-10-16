# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    ecommerce_partner_ids = fields.One2many(
        string="Ecommerce Partners",
        comodel_name="ecommerce.partner",
        inverse_name="partner_id",
    )
