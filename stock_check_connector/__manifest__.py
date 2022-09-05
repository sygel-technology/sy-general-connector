# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Check Connector",
    "summary": "Stock Check Connector",
    "version": "14.0.1.0.0",
    "category": "Stock",
    "author": "Sygel",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
        "ecommerce_connector",
    ],
    "data": [
        "views/res_company_views.xml",
    ],
}
