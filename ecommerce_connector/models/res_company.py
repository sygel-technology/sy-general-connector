# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    accept_ecommerce_connector = fields.Boolean(
        string="Accept Ecommerce Connector"
    )
    ecommerce_connector_create_invoice = fields.Boolean(
        string="Create Invoice"
    )
    ecommerce_connector_validate_invoice = fields.Boolean(
        string="Validate Invoice"
    )
    sale_order_type_id = fields.Many2one(
        comodel_name="sale.order.type",
        name="Sale Order Type"
    )
    search_name_lang = fields.Selection(
        lambda self: self._get_lang_selection_options(),
        "Search Name Lang.",
    )
    product_search_rule = fields.Selection([
        ("ecommerce_id", "Ecommerce ID"),
        ("sku", "SKU"),
        ("barcode", "Barcode")
    ],
        string="Product Search Rule",
        default="ecommerce_id"
    )
    contact_search_rule = fields.Selection([
        ("ecommerce_id", "Ecommerce ID"),
        ("email", "Email"),
        ("vat", "VAT"),
        ("contact_info", "Contact Info")
    ],
        string="Contact Search Rule",
        default="ecommerce_id"
    )
    shipping_address_search_rule = fields.Selection([
        ("ecommerce_id", "Ecommerce ID"),
        ("email", "Email"),
        ("contact_info", "Contact Info")
    ],
        string="Shipping Address Search Rule",
        default="ecommerce_id"
    )
    invoice_address_search_rule = fields.Selection([
        ("ecommerce_id", "Ecommerce ID"),
        ("email", "Email"),
        ("contact_info", "Contact Info")
    ],
        string="Invoice Address Search Rule",
        default="ecommerce_id"
    )

    @api.model
    def _get_lang_selection_options(self):
        """Gets the available languages for the selection."""
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]
