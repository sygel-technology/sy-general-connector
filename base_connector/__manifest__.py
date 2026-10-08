# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base Connector",
    "summary": "Base of the general connector modules",
    "version": "18.0.1.0.0",
    "category": "Base",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-general-connector",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "product",  # TODO: Seguro?
        "base_vat",  # TODO: Seguro?

    ],
    "data": [
        "security/ecommerce_connector_security.xml",
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
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
