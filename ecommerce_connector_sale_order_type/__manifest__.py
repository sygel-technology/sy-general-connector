# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ecommerce Connector - Sale Order Type",
    "summary": "Set a default sale type for ecommerce sale orders.",
    "version": "15.0.1.0.0",
    "category": "Ecommerce",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-general-connector",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "ecommerce_connector",
        "sale_order_type",
    ],
    "data": [
        "views/ecommerce_connection_views.xml",
    ],
}
