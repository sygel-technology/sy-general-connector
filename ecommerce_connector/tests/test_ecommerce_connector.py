# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestEcommerceConnector(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure company
        cls.company = cls.env.ref("base.demo_company_es")
        cls.company.accept_ecommerce_connector = True
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        cls.env["res.lang"]._activate_lang("es_ES")

        # Configure connector
        cls.connection_config = cls.env["ecommerce.connection"].create(
            {
                "name": "Test",
                "ecommerce_id": 1,
                "lang": "es_ES",
                "create_invoice": True,
                "validate_invoice": True,
            }
        )

        # Configure sale data
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        pay_method = cls.env["account.payment.method"].create(
            {
                "name": "Test",
                "code": "test",
                "payment_type": "inbound",
            }
        )
        journal = cls.env["account.journal"].create(
            {
                "name": "Test",
                "code": "Test",
                "type": "bank",
                "company_id": cls.company.id,
            }
        )
        cls.pay_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Direct bank transfer",  # Name must be equal to received
                "company_id": cls.company.id,
                "bank_account_link": "fixed",
                "payment_method_id": pay_method.id,
                "fixed_journal_id": journal.id,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Envío España",  # Name must be equal to received
                "product_id": cls.env.ref("delivery.product_product_delivery").id,
            }
        )
        cls.pricelist_id = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist EUR",
                "currency_id": cls.eur.id,
                "ecommerce_connector_default_currency": True,
            }
        )

    def test_create_sale_invoice_refund(self):
        with file_open(
            "ecommerce_connector/tests/request_data/create_sale.json", "r"
        ) as f:
            sale_data = json.load(f)
            sale_data["companyId"] = self.company.id
            res = self.env["ecommerce.connector"].external_create_sale(sale_data)
            self.assertEqual(res["status"], "OK")
            sale = self.env["sale.order"].browse(res["result"]["sale_id"])
            self.assertTrue(sale.exists())
            invoice = self.env["account.move"].browse(res["result"]["invoice_id"])
            self.assertTrue(invoice.exists())

        with file_open(
            "ecommerce_connector/tests/request_data/create_credit_note.json", "r"
        ) as f:
            sale_data = json.load(f)
            sale_data["companyId"] = self.company.id
            res = self.env["ecommerce.connector"].external_create_credit_note(sale_data)
            self.assertEqual(res["status"], "OK")
            credit_note = self.env["account.move"].browse(
                res["result"]["credit_note_id"]
            )
            self.assertTrue(credit_note.exists())
