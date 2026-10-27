# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestBaseConnector(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure company
        cls.company = cls.env.ref("base.main_company")
        cls.company.accept_ecommerce_connector = True
        cls.env["res.lang"]._activate_lang("es_ES")
        # Create connector configuration record
        cls.connection_config = cls.env["ecommerce.connection"].create(
            {
                "name": "Test",
                "ecommerce_id": 1,
                "lang": "es_ES",
            }
        )

    def test_create_customer(self):
        with file_open(
            "base_connector/tests/request_data/create_customer.json", "r"
        ) as f:
            customer_data = json.load(f)
            res = self.env["ecommerce.connector"].external_create_customer(
                customer_data
            )
            self.assertEqual(res["status"], "OK")
            self.assertTrue(
                self.env["res.partner"].browse(res["result"]["partner_id"]).exists()
            )

    def _create_customer(self):
        with file_open(
            "base_connector/tests/request_data/create_customer.json", "r"
        ) as f:
            customer_data = json.load(f)
            self.env["ecommerce.connector"].external_create_customer(customer_data)

    def test_read_customer(self):
        self._create_customer()
        with file_open(
            "base_connector/tests/request_data/read_customer.json", "r"
        ) as f:
            customer_data = json.load(f)
            res = self.env["ecommerce.connector"].external_read_customer(customer_data)
            self.assertEqual(res["status"], "OK")
            self.assertTrue(res["result"])

    def test_update_customer(self):
        self._create_customer()
        with file_open(
            "base_connector/tests/request_data/write_customer.json", "r"
        ) as f:
            customer_data = json.load(f)
            res = self.env["ecommerce.connector"].external_update_customer(
                customer_data
            )
            self.assertEqual(res["status"], "OK")
