# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tools import file_open

from odoo.addons.base_connector.tests.test_base_connector import TestBaseConnector


class TestEcommerceConnector(TestBaseConnector):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.connection_config.create_invoice = True
        cls.connection_config.validate_invoice = True

    def test_create_sale_invoice_refund(self):
        with file_open(
            "ecommerce_connector/tests/request_data/create_sale.json", "r"
        ) as f:
            sale_data = json.load(f)
            res = self.env["ecommerce.connector"].external_create_sale(sale_data)
            self.assertTrue(res)

        with file_open(
            "ecommerce_connector/tests/request_data/create_credit_note.json", "r"
        ) as f:
            sale_data = json.load(f)
            res = self.env["ecommerce.connector"].external_create_credit_note(sale_data)
            self.assertTrue(res)
