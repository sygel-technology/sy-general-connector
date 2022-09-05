# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ecommerce Connector",
    "summary": "Ecommerce Connector",
    "version": "14.0.2.0.0",
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
        "delivery",
    ],
    "data": [
        "data/ecommerce_connector_call_seq.xml",
        "views/res_company_views.xml",
        "views/product_pricelist_views.xml",
        "views/ecommerce_connector_call_views.xml",
        "views/ecommerce_connection_views.xml",
        "views/ecommerce_product_views.xml",
        "views/ecommerce_partner_views.xml",
        "views/menuitems.xml",
        "security/ir.model.access.csv",
    ],
}
