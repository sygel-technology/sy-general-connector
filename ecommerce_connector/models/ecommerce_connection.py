# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EcommerceConnection(models.Model):
    _name = "ecommerce.connection"

    @api.model
    def _selection_languages(self):
        return self.env["res.lang"].get_installed()

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    ecommerce_id = fields.Integer(string="Ecommerce ID", required=True)
    lang = fields.Selection(
        _selection_languages,
        string="Language",
        required=True,
        help="Language used for writing operation in multilanguage fields.",
    )
    use_odoo_so_sequence = fields.Boolean(string="Use Odoo Sales Seq.")
    duplicate_invoice_name = fields.Boolean(
        string="Duplicate Name in Invoice Address",
        help="If checked, the Invoice Address name is set in case it equals "
        "the customer name. If unchecked, the Invoice Address name is left"
        "blank when it equals the Customer name.",
    )
    product_search_rule = fields.Selection(
        [("ecommerce_id", "Ecommerce ID"), ("sku", "SKU"), ("barcode", "Barcode")],
        default="ecommerce_id",
        required=True,
    )
    contact_search_partner_type = fields.Boolean(
        help="If checked, the partner type (person or company) will be "
        "used in the customer's search domain."
    )
    contact_search_rule = fields.Selection(
        [
            ("ecommerce_id", "Ecommerce ID"),
            ("email", "Email"),
            ("vat", "VAT"),
            ("contact_info", "Contact Info"),
        ],
        default="ecommerce_id",
        required=True,
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
    create_contacts_single_company = fields.Boolean(
        string="Create Contacts for Single Company"
    )
    check_customer_vat = fields.Boolean()
    create_invoice = fields.Boolean()
    invoice_policy = fields.Selection(
        [("order", "Ordered quantities"), ("delivery", "Delivered quantities")],
    )
    validate_invoice = fields.Boolean()

    _sql_constraints = [
        (
            "ecommerce_id_name_unique",
            "unique(ecommerce_id, company_id)",
            "Ecommerce ID must be unique.",
        )
    ]
