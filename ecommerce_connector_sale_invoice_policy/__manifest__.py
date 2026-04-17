# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ecommerce Connector - Sale Invoice Policy",
    "summary": "Set a default invoice policy for ecommerce sale orders.",
    "version": "18.0.1.0.0",
    "category": "Ecommerce",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-general-connector",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "ecommerce_connector",
        "sale_invoice_policy",
    ],
    "data": [
        "views/ecommerce_connection_views.xml",
    ],
}
