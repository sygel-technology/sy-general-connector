# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ecommerce Connector",
    "summary": "Ecommerce Connector",
    "version": "15.0.1.0.0",
    "category": "Custom",
    "author": "Sygel",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "account",
        "account_payment_mode",
        "account_payment_sale",
        "base_vat",
        "account_fiscal_position_partner_type",
        "l10n_es_aeat_sii_oca",
        "product",
        "sale_invoice_policy",
        "sale_order_type"
    ],
    "data": [
        "data/ecommerce_connector_call_seq.xml",
        "views/res_company_views.xml",
        "views/product_pricelist_views.xml",
        "views/ecommerce_connector_call_views.xml",
        "views/menuitems.xml",
        "views/product_views.xml",
        "security/ir.model.access.csv",
    ],
}
