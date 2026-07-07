# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ecommerce Connector",
    "summary": "General E-Commerce Integration",
    "version": "18.0.1.0.1",
    "category": "Ecommerce",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-general-connector",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_payment_mode",
        "account_payment_sale",
        "base_vat",
        "account_fiscal_position_partner_type",
        "sale_management",
        "stock_delivery",
        # "l10n_eu_oss_oca"  # Soft dependency
    ],
    "data": [
        "security/ecommerce_connector_security.xml",
        "security/ir.model.access.csv",
        "data/ecommerce_connector_call_seq.xml",
        "views/res_company_views.xml",
        "views/product_pricelist_views.xml",
        "views/ecommerce_connector_call_views.xml",
        "views/ecommerce_connection_views.xml",
        "views/ecommerce_product_views.xml",
        "views/ecommerce_partner_views.xml",
        "views/menuitems.xml",
    ],
    "demo": [
        "security/ecommerce_connector_security_demo.xml",
    ],
}
