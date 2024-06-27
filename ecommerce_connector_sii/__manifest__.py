# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ecommerce Connector - SII Simplified Invoice",
    "summary": "Set the invoice as Simplified if the customar has no VAT.",
    "version": "14.0.1.0.0",
    "category": "Custom",
    "author": "Sygel",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "ecommerce_connector",
        "l10n_es_aeat_sii_oca",
    ],
}
