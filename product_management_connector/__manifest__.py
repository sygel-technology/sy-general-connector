# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Management Connector",
    "summary": "Product Management Connector",
    "version": "14.0.1.0.0",
    "category": "Ecommerce",
    "author": "Sygel",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "ecommerce_connector",
    ],
    "data": [
        "views/res_company_views.xml",
    ],
}
