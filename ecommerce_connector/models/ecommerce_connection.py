# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EcommerceConnection(models.Model):
    _inherit = "ecommerce.connection"

    use_odoo_so_sequence = fields.Boolean(
        string="Use Odoo Sales Seq.",
        help="Use Odoo internal numbering instead of the ecommerce order reference.",
    )
    duplicate_invoice_name = fields.Boolean(
        string="Duplicate Name in Invoice Address",
        help="If checked, the Invoice Address name is set in case it equals "
        "the customer name. If unchecked, the Invoice Address name is left"
        "blank when it equals the Customer name.",
    )
    shipping_address_search_rule = fields.Selection(
        [
            ("ecommerce_id", "Ecommerce ID"),
            ("email", "Email"),
            ("contact_info", "Contact Info"),
        ],
        default="ecommerce_id",
        required=True,
    )
    invoice_address_search_rule = fields.Selection(
        [
            ("ecommerce_id", "Ecommerce ID"),
            ("email", "Email"),
            ("contact_info", "Contact Info"),
        ],
        default="ecommerce_id",
        required=True,
    )
    create_products_single_company = fields.Boolean(
        string="Create Products for Single Company"
    )
    create_invoice = fields.Boolean(
        help="Automatically create an invoice when the order is imported."
    )
    validate_invoice = fields.Boolean(
        help="Automatically validate the invoice after creation."
    )
    update_contacts = fields.Boolean(
        help="If checked, the searched contacts will be updated "
        "with the remaining partner data of the request"
    )
