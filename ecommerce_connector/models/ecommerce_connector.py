# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from base64 import b64encode
from datetime import datetime

from odoo import api, fields, models
from odoo.tools import float_compare


class EcommerceConnector(models.Model):
    _name = "ecommerce.connector"
    _description = "Ecommerce Connector"

    def _write_errors(self, errors, new_error):
        """Returns errors string after adding a new error

        :param errors: string with current errors
        :param new_error: string with new error to be added
        """
        return f"{errors}{new_error}\n"

    def get_country(self, code):
        """Returns country record identified by the code

        :param code: string with country code
        """
        country_id = False
        if code:
            country_id = self.env["res.country"].search([("code", "=", code)], limit=1)
        return country_id

    def get_province(self, country, code):
        """Returns province record associated to given country and code

        :param country: record of res.country
        :param code: string with province code
        """
        province_id = self.env["res.country.state"]
        if country and code:
            province_id = self.env["res.country.state"].search(
                [("country_id", "=", country.id), ("code", "=", code)], limit=1
            )
        return province_id

    def _get_contact_domain(self, values, ecommerce_connection):
        domain = []
        is_company = values.get("customer").get("typeClient") == "business"
        if ecommerce_connection.contact_search_rule == "ecommerce_id":
            ecommerce_partner_id = self.env["ecommerce.partner"].search(
                [
                    ("ecommerce_connection_id", "=", ecommerce_connection.id),
                    ("ecommerce_id", "=", int(values.get("customer").get("id"))),
                ],
                limit=1,
            )
            if ecommerce_partner_id:
                contact_type = (
                    "person"
                    if values.get("customer").get("typeClient") == "individual"
                    else "company"
                )
                if (
                    ecommerce_connection.contact_search_partner_type
                    and ecommerce_partner_id.partner_id.company_type == contact_type
                ) or not ecommerce_connection.contact_search_partner_type:
                    domain = ["id", "=", ecommerce_partner_id.partner_id.id]
        elif ecommerce_connection.contact_search_rule == "email":
            domain = [
                ("email", "=ilike", values.get("customer").get("email")),
                ("parent_id", "=", False),
                ("company_id", "in", [False, int(values.get("companyId"))]),
            ]
            if ecommerce_connection.contact_search_partner_type:
                domain += [("is_company", "=", is_company)]
        elif ecommerce_connection.contact_search_rule == "vat":
            domain = [
                ("parent_id", "=", False),
                ("company_id", "in", [False, int(values.get("companyId"))]),
            ]
            if ecommerce_connection.contact_search_partner_type:
                domain += [("is_company", "=", is_company)]
            vat = values.get("customer").get("vat")
            vat_domain = [("vat", "=ilike", vat)]
            country_id = self.get_country(
                values.get("shippingAddress").get("countryCode")
            )
            if country_id:
                if vat.startswith(country_id.code):
                    vat_with_code = vat
                    vat = vat[len(country_id.code) :]
                else:
                    vat_with_code = "{}{}".format(country_id.code, vat)
                vat_domain = [
                    "|",
                    ("vat", "=ilike", vat),
                    ("vat", "=ilike", vat_with_code),
                ]
            domain = vat_domain + domain
        elif ecommerce_connection.contact_search_rule == "contact_info":
            name = ""
            if is_company:
                name = values.get("customer").get("comercialName")
            else:
                name = values.get("customer").get("firstname")
                if values.get("customer").get("lastname"):
                    name = "%s %s" % (name, values.get("customer").get("lastname"))
            domain = [
                ("parent_id", "=", False),
                ("name", "=ilike", name),
                ("email", "=ilike", values.get("customer").get("email")),
                (
                    "phone",
                    "=ilike",
                    values.get("customer").get("phone")
                    if values.get("customer").get("phone") is not None
                    else False,
                ),
                (
                    "mobile",
                    "=ilike",
                    values.get("customer").get("mobile")
                    if values.get("customer").get("mobile") is not None
                    else False,
                ),
                (
                    "vat",
                    "=ilike",
                    values.get("customer").get("vat")
                    if values.get("customer").get("vat") is not None
                    else False,
                ),
                ("company_id", "in", [False, int(values.get("companyId"))]),
            ]
            if ecommerce_connection.contact_search_partner_type:
                domain += [("is_company", "=", is_company)]
        return domain

    def _get_contact(self, values, ecommerce_connection):
        """Returns a res.partner record with the given values

        :param values: dictionary with the contact data
        :param ecommerce_connection: ecommerce.connection record
        """
        partner_id = False
        domain = self._get_contact_domain(values, ecommerce_connection)
        if domain:
            partner_id = self.env["res.partner"].search(
                domain,
                limit=1,
            )
        if not partner_id:
            partner_id = self._create_new_partner(values, ecommerce_connection)
        return partner_id

    def _get_shipping_contact(self, partner, values, ecommerce_connection):
        """Returns a res.partner record of 'delivery' type with the given values

        :param partner: parent res.partner record
        :param values: dictionary with the contact data
        :param ecommerce_connection: ecommerce.connection record
        """
        partner_id = False
        if ecommerce_connection.shipping_address_search_rule == "ecommerce_id":
            ecommerce_partner_id = self.env["ecommerce.partner"].search(
                [
                    ("ecommerce_connection_id", "=", ecommerce_connection.id),
                    ("ecommerce_id", "=", int(values.get("shippingAddress").get("id"))),
                ],
                limit=1,
            )
            if (
                ecommerce_partner_id
                and ecommerce_partner_id.partner_id.type == "delivery"
                and ecommerce_partner_id.partner_id.parent_id == partner
            ):
                partner_id = ecommerce_partner_id.partner_id
        elif ecommerce_connection.shipping_address_search_rule == "email":
            partner_id = partner.child_ids.filtered(
                lambda a: a.type == "delivery"
                and a.email == values.get("shippingAddress").get("email")
            )
        elif ecommerce_connection.shipping_address_search_rule == "contact_info":
            name = values.get("shippingAddress").get("firstname")
            if values.get("shippingAddress").get("lastname"):
                name = "{} {}".format(
                    name, values.get("shippingAddress").get("lastname")
                )
            country_id = self.get_country(
                values.get("shippingAddress").get("countryCode")
            )
            province_id = self.get_province(
                country_id, values.get("shippingAddress").get("provinceCode")
            )
            partner_id = partner.child_ids.filtered(
                lambda a: a.type == "delivery"
                and a.name == name
                and a.country_id == country_id
                and a.state_id == province_id
                and a.street == values.get("shippingAddress").get("street")
                and a.street2
                == (
                    values.get("shippingAddress").get("street2")
                    if values.get("shippingAddress").get("street2") is not None
                    else False
                )
                and a.city
                == (
                    values.get("shippingAddress").get("city")
                    if values.get("shippingAddress").get("city") is not None
                    else False
                )
                and a.zip == values.get("shippingAddress").get("postcode")
                and a.email
                == (
                    values.get("shippingAddress").get("email")
                    if values.get("shippingAddress").get("email") is not None
                    else False
                )
                and a.phone
                == (
                    values.get("shippingAddress").get("phone")
                    if values.get("shippingAddress").get("phone") is not None
                    else False
                )
                and a.mobile
                == (
                    values.get("shippingAddress").get("mobile")
                    if values.get("shippingAddress").get("mobile") is not None
                    else False
                )
            )
        if not partner_id:
            partner_id = self._create_new_shipping_partner(
                values, partner, ecommerce_connection
            )
        else:
            partner_id = partner_id[0]
        return partner_id

    def _get_invoice_contact(self, partner, values, ecommerce_connection):
        """Returns a res.partner record of 'invoice' type with the given values

        :param partner: parent res.partner record
        :param values: dictionary with the contact data
        :param ecommerce_connection: ecommerce.connection record
        """
        partner_id = False
        if ecommerce_connection.invoice_address_search_rule == "ecommerce_id":
            ecommerce_partner_id = self.env["ecommerce.partner"].search(
                [
                    ("ecommerce_connection_id", "=", ecommerce_connection.id),
                    ("ecommerce_id", "=", int(values.get("billingAddress").get("id"))),
                ],
                limit=1,
            )
            if (
                ecommerce_partner_id
                and ecommerce_partner_id.partner_id.type == "invoice"
                and ecommerce_partner_id.partner_id.parent_id == partner
            ):
                partner_id = ecommerce_partner_id.partner_id
        elif ecommerce_connection.invoice_address_search_rule == "email":
            partner_id = partner.child_ids.filtered(
                lambda a: a.type == "invoice"
                and a.email == values.get("billingAddress").get("email")
            )
        elif ecommerce_connection.invoice_address_search_rule == "contact_info":
            name = values.get("billingAddress").get("firstname")
            if values.get("billingAddress").get("lastname"):
                name = "{} {}".format(
                    name, values.get("billingAddress").get("lastname")
                )
            country_id = self.get_country(
                values.get("billingAddress").get("countryCode")
            )
            province_id = self.get_province(
                country_id, values.get("billingAddress").get("provinceCode")
            )
            accepted_names = [name]
            if (
                not ecommerce_connection.duplicate_invoice_name
                and partner.name.upper() == name.upper()
            ):
                # It is necessary to include both '' and False
                accepted_names += [False, ""]

            partner_id = partner.child_ids.filtered(
                lambda a: a.type == "invoice"
                and a.name in accepted_names
                and a.country_id == country_id
                and a.state_id == province_id
                and a.street == values.get("billingAddress").get("street")
                and a.street2
                == (
                    values.get("billingAddress").get("street2")
                    if values.get("billingAddress").get("street2") is not None
                    else False
                )
                and a.city
                == (
                    values.get("billingAddress").get("city")
                    if values.get("billingAddress").get("city") is not None
                    else False
                )
                and a.zip == values.get("billingAddress").get("postcode")
                and a.email
                == (
                    values.get("billingAddress").get("email")
                    if values.get("billingAddress").get("email") is not None
                    else False
                )
                and a.phone
                == (
                    values.get("billingAddress").get("phone")
                    if values.get("billingAddress").get("phone") is not None
                    else False
                )
                and a.mobile
                == (
                    values.get("billingAddress").get("mobile")
                    if values.get("billingAddress").get("mobile") is not None
                    else False
                )
            )
        if not partner_id:
            partner_id = self._create_new_invoice_partner(
                values, partner, ecommerce_connection
            )
        else:
            partner_id = partner_id[0]
        return partner_id

    def _get_national_fiscal_position(self, country, company):
        """Returns an account.fiscal.position record with the basic fiscal position
            of a given country

        :param country: res.country record
        :param company: res.company record
        """
        fiscal_position_id = False
        if country.code.upper() == "ES":
            fiscal_position_id = self.env.ref("l10n_es.%s_fp_nacional" % company.id)
        elif country.code.upper() == "FR":
            fiscal_position_id = self.env.ref(
                "l10n_fr.%s_fiscal_position_template_domestic" % company.id
            )
        return fiscal_position_id

    def _get_intra_fp(self, country, company):
        """Returns an account.fiscal.position record

        :param country: res.country record
        :param company: res.company record
        """
        fiscal_position_id = False
        if country.code.upper() == "ES":
            fiscal_position_id = self.env.ref("l10n_es.%s_fp_intra" % company.id)
        elif country.code.upper() == "FR":
            fiscal_position_id = self.env.ref(
                "l10n_fr.%s_fiscal_position_template_intraeub2b" % company.id
            )
        return fiscal_position_id

    def _get_extra_fp(self, country, company):
        """Returns an account.fiscal.position record

        :param country: res.country record
        :param company: res.company record
        """
        fiscal_position_id = False
        if country.code.upper() == "ES":
            fiscal_position_id = self.env.ref("l10n_es.%s_fp_extra" % company.id)
        elif country.code.upper() == "FR":
            fiscal_position_id = self.env.ref(
                "l10n_fr.%s_fiscal_position_template_import_export" % company.id
            )
        return fiscal_position_id

    def _get_national_tax_rates(self, country):
        """Returns a list containing the VAT rates of a given country

        :param country: res.country record
        """
        tax_rates = []
        if country.code.upper() == "ES":
            tax_rates = [21.00, 10.00, 4.00]
        elif country.code.upper() == "FR":
            tax_rates = [20.00, 10.00, 5.50, 2.10]
        return tax_rates

    def _get_fiscal_position(self, country, delivery_address, values, company):
        """Returns an account.fiscal.position record

        :param country: res.country record of the company country
        :param delivery_address: res.partner record with the delivery address
        :param values: dictionary with the sale data
        :param company: res.company record of the current company
        """
        tax_rate = values.get("lines")[0].get("taxes")[0].get("taxRate")
        fiscal_position_id = False
        national_fp = self._get_national_fiscal_position(country, company)
        europe_group = self.env.ref("base.europe").country_ids - country
        # In case l10n_eu_oss module is installed
        if (
            hasattr(self.env["account.fiscal.position"], "oss_oca")
            and tax_rate != 0.0
            and delivery_address.country_id.id in europe_group.ids
        ):
            fiscal_position_id = self.env["account.fiscal.position"].search(
                [
                    ("oss_oca", "=", True),
                    ("country_id", "=", delivery_address.country_id.id),
                    ("fiscal_position_type", "=", "b2c"),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
        elif tax_rate != 0.0 and delivery_address.country_id == company.country_id:
            fiscal_position_id = national_fp
        # This is because of the UK for now
        elif tax_rate != 0.0:
            fiscal_position_id = self.env["account.fiscal.position"].search(
                [
                    ("country_id", "=", delivery_address.country_id.id),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
        # Intracomunicatio B2B
        elif tax_rate == 0.0 and delivery_address.country_id.id in europe_group.ids:
            fiscal_position_id = self._get_intra_fp(country, company)
        # Extracomunitario
        elif tax_rate == 0.0 and delivery_address.country_id.id not in europe_group.ids:
            fiscal_position_id = self._get_extra_fp(country, company)
        if fiscal_position_id and fiscal_position_id != national_fp:
            taxes = fiscal_position_id.tax_ids.mapped("tax_dest_id")
            if tax_rate not in taxes.mapped("amount"):
                fiscal_position_id = False
        if (
            not fiscal_position_id
            and national_fp
            and (tax_rate in self._get_national_tax_rates(country))
        ):
            fiscal_position_id = national_fp
        return fiscal_position_id

    def _get_order_line(self, fiscal_position, line, ecommerce_connection):
        """Returns a dictionary with values for a new order line

        :param fiscal_position: account.fiscal.position record with the
            applied fiscal position
        :param line: dictionary with the order line info
        :param ecommerce_connection: record or ecommerce.connection
        """
        company = ecommerce_connection.company_id.id
        product_id = self._find_product(line, ecommerce_connection)
        taxes = (
            fiscal_position.with_company(company)
            .map_tax(product_id.taxes_id)
            .filtered(lambda a: a.company_id.id == company)
        )
        values = {
            "product_id": product_id.id if product_id else False,
            "product_uom_qty": line.get("quantity"),
            "price_unit": line.get("unitPrice"),
            "discount": line.get("discount"),
            "tax_id": taxes,
            "ecommerce_id": line.get("id"),
        }
        if line.get("description"):
            values["name"] = line.get("description")
        return values

    def _get_shipment_line(self, fiscal_position, shipment, company):
        """Returns a dictionary with values for a new order line,
            containing shipping info

        :param fiscal_position: account.fiscal.position record with the
            applied fiscal position
        :param shipment: dictionary with the order line info
        :param company: record of res.company
        """
        delivery_carrier_id = self.env["delivery.carrier"].search(
            [("name", "=ilike", shipment.get("method"))], limit=1
        )
        taxes = (
            fiscal_position.with_company(company)
            .map_tax(delivery_carrier_id.product_id.taxes_id)
            .filtered(lambda a: a.company_id.id == company)
        )
        return {
            "product_id": delivery_carrier_id.product_id.id,
            "name": shipment.get("method"),
            "product_uom_qty": 1,
            "price_unit": shipment.get("unitPrice"),
            "tax_id": taxes.ids,
            "ecommerce_shipping_id": shipment.get("id"),
        }

    def _get_order_lines(self, fiscal_position_id, values, ecommerce_connection):
        """Returns a dictionary with values of all the lines of the new sale

        :param fiscal_position_id: account.fiscal.position record with the
            applied fiscal position
        :param values: dictionary with the order lines info
        :param ecommerce_connection: record of ecommerce.connection
        """
        company = ecommerce_connection.company_id.id
        order_lines = []
        for line in values.get("lines"):
            order_lines.append(
                (
                    0,
                    0,
                    self._get_order_line(
                        fiscal_position_id, line, ecommerce_connection
                    ),
                )
            )
        if values.get("shipments"):
            for shipment in values.get("shipments"):
                order_lines.append(
                    (
                        0,
                        0,
                        self._get_shipment_line(fiscal_position_id, shipment, company),
                    )
                )

        return order_lines

    def _get_credit_note_line(self, line, ecommerce_connection):
        """Returns a dictionary with values of all the lines of a new credit note

        :param line: dictionary with the credit note line info
        :param ecommerce_connection: record of ecommerce.connection
        """
        product_id = self._find_product(line, ecommerce_connection)
        return {
            "product_id": product_id.id,
            "price_unit": line.get("unitPrice"),
            "quantity": line.get("quantity"),
        }

    def _get_credit_note_lines(self, lines, ecommerce_connection):
        """Returns a dictionary with values of all the credit note lines

        :param lines: list of dictionaries with the credit note line info
        :param ecommerce_connection: record of ecommerce.connection
        """
        credit_note_lines = []
        for line in lines:
            credit_note_lines.append(
                (0, 0, self._get_credit_note_line(line, ecommerce_connection))
            )
        return credit_note_lines

    def _check_general_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if not values.get("id"):
            errors = self._write_errors(errors, "Ecommerce ID is missing.")
        if "number" not in excluded_fields and not values.get("number"):
            errors = self._write_errors(errors, "Ecommerce number is missing.")
        if not values.get("companyId"):
            errors = self._write_errors(errors, "Company is missing.")
        if "origin" not in excluded_fields and not values.get("origin"):
            errors = self._write_errors(errors, "Origin is missing.")
        if not values.get("currencyCode"):
            errors = self._write_errors(errors, "Currency code is missing.")
        if not values.get("exchangeRate"):
            errors = self._write_errors(errors, "Exchange rate is missing.")
        if not values.get("total"):
            errors = self._write_errors(errors, "Total is missing.")
        if not values.get("totalCompany"):
            errors = self._write_errors(errors, "Total company is missing.")
        if values.get("taxTotal") is None:
            errors = self._write_errors(errors, "Tax total is missing.")
        if values.get("taxTotalCompany") is None:
            errors = self._write_errors(errors, "Tax total company is missing.")
        if values.get("shippingTotal") is None:
            errors = self._write_errors(errors, "Shipping total is missing.")
        if values.get("shippingTotalCompany") is None:
            errors = self._write_errors(errors, "Shipping total company is missing.")
        if not values.get("dateOrder"):
            errors = self._write_errors(errors, "Date order is missing.")
        return errors

    def _check_customer_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if not values.get("customer"):
            errors = self._write_errors(errors, "Customer is missing.")
        if "customer.id" not in excluded_fields and not values.get("customer").get(
            "id"
        ):
            errors = self._write_errors(errors, "Ecommerce Customer ID is missing.")
        if not values.get("customer").get("firstname"):
            errors = self._write_errors(errors, "Customer firstname is missing.")
        if "customer.email" not in excluded_fields and not values.get("customer").get(
            "email"
        ):
            errors = self._write_errors(errors, "Customer email is missing.")
        if not values.get("customer").get("typeClient"):
            errors = self._write_errors(errors, "Customer type client is missing.")
        if (
            "customer.vat" not in excluded_fields
            and values.get("customer").get("typeClient") == "business"
            and not values.get("customer").get("vat")
        ):
            errors = self._write_errors(errors, "Customer VAT is missing.")
        return errors

    def _check_shipping_address_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if not values.get("shippingAddress"):
            errors = self._write_errors(errors, "Shipping address is missing.")
        if "shippingAddress.id" not in excluded_fields and not values.get(
            "shippingAddress"
        ).get("id"):
            errors = self._write_errors(
                errors, "Ecommerce shipping address ID is missing."
            )
        if "shippingAddress.firstname" not in excluded_fields and not values.get(
            "shippingAddress"
        ).get("firstname"):
            errors = self._write_errors(
                errors, "Shipping address firstname is missing."
            )
        if "shippingAddress.countryCode" not in excluded_fields and not values.get(
            "shippingAddress"
        ).get("countryCode"):
            errors = self._write_errors(
                errors, "Shipping address country code is missing."
            )
        if "shippingAddress.street" not in excluded_fields and not values.get(
            "shippingAddress"
        ).get("street"):
            errors = self._write_errors(errors, "Shipping address street is missing.")
        if "shippingAddress.postcode" not in excluded_fields and not values.get(
            "shippingAddress"
        ).get("postcode"):
            errors = self._write_errors(errors, "Shipping address postcode is missing.")
        return errors

    def _check_billing_address_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if not values.get("billingAddress"):
            errors = self._write_errors(errors, "Billing address is missing.")
        if "billingAddress.id" not in excluded_fields and not values.get(
            "billingAddress"
        ).get("id"):
            errors = self._write_errors(
                errors, "Ecommerce billing address ID is missing."
            )
        if "billingAddress.firstname" not in excluded_fields and not values.get(
            "billingAddress"
        ).get("firstname"):
            errors = self._write_errors(errors, "Billing address firstname is missing.")
        if "billingAddress.countryCode" not in excluded_fields and not values.get(
            "billingAddress"
        ).get("countryCode"):
            errors = self._write_errors(
                errors, "Billing address country code is missing."
            )
        if "billingAddress.street" not in excluded_fields and not values.get(
            "billingAddress"
        ).get("street"):
            errors = self._write_errors(errors, "Billing address street is missing.")
        if "billingAddress.postcode" not in excluded_fields and not values.get(
            "billingAddress"
        ).get("postcode"):
            errors = self._write_errors(errors, "Billing address postcode is missing.")
        return errors

    def _check_payment_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if values.get("payments"):
            if any(
                not payment.get("id")
                or not payment.get("method")
                or not payment.get("unitPrice")
                or not payment.get("unitPriceCompany")
                for payment in values.get("payments")
            ):
                errors = self._write_errors(
                    errors,
                    "Ecommerce ID, method, unit price and unit price company "
                    "are mandatory for all payments.",
                )
        return errors

    def _check_shipment_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if values.get("shipments"):
            if any(
                not shipment.get("id")
                or not shipment.get("method")
                or shipment.get("unitPrice") is None
                or shipment.get("unitPriceCompany") is None
                for shipment in values.get("shipments")
            ):
                errors = self._write_errors(
                    errors,
                    "Ecommerce ID, method, unit price and unit price company "
                    "are mandatory for all shipments.",
                )
        return errors

    def _check_lines_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if not values.get("lines"):
            errors = self._write_errors(errors, "Lines are missing.")
        if any(
            not line.get("productName")
            or not line.get("productId")
            or not line.get("productTemplateId")
            or ("line.productSku" not in excluded_fields and not line.get("productSku"))
            or (
                "line.productBarcode" not in excluded_fields
                and not line.get("productBarcode")
            )
            or not line.get("productTaxCompany")
            or not line.get("productType")
            or not line.get("id")
            or not line.get("quantity")
            or not line.get("unitPrice")
            or not line.get("unitPriceCompany")
            or not line.get("total")
            or not line.get("totalCompany")
            or not line.get("subtotal")
            or not line.get("subtotalCompany")
            or ("line.taxes" not in excluded_fields and not line.get("taxes"))
            for line in values.get("lines")
        ):
            errors = self._write_errors(
                errors,
                "All fields but discount, description, product description or "
                "variant in lines are mandatory.",
            )

        for line in values.get("lines"):
            if any(
                ("tax.taxId" not in excluded_fields and tax.get("taxId") is None)
                or ("tax.taxName" not in excluded_fields and not tax.get("taxName"))
                or tax.get("taxRate") is None
                for tax in line.get("taxes")
            ):
                errors = self._write_errors(
                    errors, "Tax ID, tax name,and tax rate are mandatory for all taxes."
                )
        return errors

    def _check_product_search_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if ecommerce_connection.product_search_rule == "barcode" and any(
            not line.get("productBarcode") for line in values.get("lines")
        ):
            errors = self._write_errors(
                errors,
                "Products are searched by barcode. All products need to have a"
                " barcode.",
            )
        return errors

    def _check_customer_search_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if ecommerce_connection.contact_search_rule == "vat" and not values.get(
            "customer"
        ).get("vat"):
            errors = self._write_errors(
                errors, "Customer is searched by VAT but it is not provided."
            )
        return errors

    def _check_billing_address_search_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if (
            ecommerce_connection.invoice_address_search_rule == "ecommerce_id"
            and not values.get("billingAddress").get("id")
        ):
            errors = self._write_errors(
                errors, "Billing address is searched by id but it is not provided."
            )
        if (
            ecommerce_connection.invoice_address_search_rule == "email"
            and not values.get("billingAddress").get("email")
        ):
            errors = self._write_errors(
                errors, "Billing address is searched by email but it is not provided."
            )
        return errors

    def _check_shipping_address_search_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if (
            ecommerce_connection.shipping_address_search_rule == "ecommerce_id"
            and not values.get("shippingAddress").get("id")
        ):
            errors = self._write_errors(
                errors, "Shipping address is searched by id but it is not provided."
            )
        if (
            ecommerce_connection.shipping_address_search_rule == "email"
            and not values.get("shippingAddress").get("email")
        ):
            errors = self._write_errors(
                errors, "Shipping address is searched by email but it is not provided."
            )
        return errors

    def _check_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with the values to be checked
        :param company_id: res.company record
        :param ecommerce_connection: ecommerce.connection record
        :param excluded_fields: list of mandatory fields to be excluded
        """
        # General mandatory fields
        errors = self._check_general_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Mandatory fields Customer
        errors = self._check_customer_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Mandatory fields shipping address
        errors = self._check_shipping_address_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Mandatory fields billing address
        errors = self._check_billing_address_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Mandatory fields payment
        errors = self._check_payment_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Mandatory fields shipments
        errors = self._check_shipment_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Mandatory fields lines
        errors = self._check_lines_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Missing search fields for products
        errors = self._check_product_search_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Missing search fields for customer
        errors = self._check_customer_search_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Missing search fields for billing address
        errors = self._check_billing_address_search_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        # Missing search fields for shiping address
        errors = self._check_shipping_address_search_mandatory_fields(
            errors, values, company_id, ecommerce_connection, excluded_fields
        )

        return errors

    def _check_has_country(self, errors, company_id):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param company_id: res.company record to be checked
        """
        if not company_id.country_id:
            errors = self._write_errors(errors, "Company has no country.")
        return errors

    def _check_company(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: values to be checked
        """
        if values.get("companyId"):
            if not self.env["res.company"].search(
                [("id", "=", int(values.get("companyId")))]
            ):
                errors = self._write_errors(errors, "Company not found.")
        return errors

    def _check_payments(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: values to be checked
        """
        if values.get("payments"):
            # Check the total amount paid
            amount_paid = sum(
                float(payment.get("unitPrice")) for payment in values.get("payments")
            )
            if amount_paid > float(values.get("total")):
                errors = self._write_errors(
                    errors, "Paid amount cannot be higher than total amount."
                )
            for payment in values.get("payments"):
                payment_mode_id = self.env["account.payment.mode"].search(
                    [
                        ("name", "=ilike", payment.get("method")),
                        ("company_id", "=", int(values.get("companyId"))),
                    ],
                    limit=1,
                )
                if not payment_mode_id:
                    errors = self._write_errors(
                        errors,
                        "%s payment mode is not in the system." % payment.get("method"),
                    )
                elif (
                    payment_mode_id.bank_account_link != "fixed"
                    or not payment_mode_id.fixed_journal_id
                ):
                    errors = self._write_errors(
                        errors,
                        "%s payment mode needs to be associated to one journal."
                        % payment.get("method"),
                    )
        return errors

    def _check_shipments(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        if values.get("shipments"):
            for shipment in values.get("shipments"):
                if not self.env["delivery.carrier"].search(
                    [("name", "=ilike", shipment.get("method"))], limit=1
                ):
                    errors = self._write_errors(
                        errors,
                        "%s shipment method is not in the system."
                        % shipment.get("method"),
                    )
        return errors

    def _check_customer_country_province(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        if (
            values.get("customer")
            and values.get("customer").get("countryCode")
            and values.get("customer").get("provinceCode")
        ):
            country_id = self.get_country(values.get("customer").get("countryCode"))
            if not country_id:
                errors = self._write_errors(errors, "Customer country not found.")
            else:
                province_id = self.get_province(
                    country_id, values.get("customer").get("provinceCode")
                )
                if not province_id:
                    errors = self._write_errors(errors, "Customer province not found.")
        return errors

    def _check_shipping_country_province(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        if (
            values.get("shippingAddress")
            and values.get("shippingAddress").get("countryCode")
            and values.get("shippingAddress").get("provinceCode")
        ):
            country_id = self.get_country(
                values.get("shippingAddress").get("countryCode")
            )
            if not country_id:
                errors = self._write_errors(
                    errors, "Shipping address country not found."
                )
            else:
                province_id = self.get_province(
                    country_id, values.get("shippingAddress").get("provinceCode")
                )
                if not province_id:
                    errors = self._write_errors(
                        errors, "Shipping address province not found."
                    )
        return errors

    def _check_billing_country_province(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        if (
            values.get("billingAddress")
            and values.get("billingAddress").get("countryCode")
            and values.get("billingAddress").get("provinceCode")
        ):
            country_id = self.get_country(
                values.get("billingAddress").get("countryCode")
            )
            if not country_id:
                errors = self._write_errors(
                    errors, "Billing address country not found."
                )
            else:
                province_id = self.get_province(
                    country_id, values.get("billingAddress").get("provinceCode")
                )
                if not province_id:
                    errors = self._write_errors(
                        errors, "Billing address province not found."
                    )
        return errors

    def _check_lang(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        if values.get("customer") and values.get("customer").get("languageCode"):
            lang = self.env["res.lang"].search(
                [
                    ("code", "=", values.get("customer").get("languageCode")),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if not lang:
                errors = self._write_errors(errors, "Language not found.")
        return errors

    def _check_currency(self, errors, values, company):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        :param company: res.company record
        """
        if values.get("currencyCode"):
            currency_id = self.env["res.currency"].search(
                [("name", "=", values.get("currencyCode")), ("active", "=", True)],
                limit=1,
            )
            if not currency_id:
                errors = self._write_errors(errors, "Currency not found.")
            elif currency_id != company.currency_id:
                pricelist_id = self.env["product.pricelist"].search(
                    [
                        ("ecommerce_connector_default_currency", "=", True),
                        ("currency_id", "=", currency_id.id),
                    ],
                    limit=1,
                )
                if not pricelist_id:
                    errors = self._write_errors(errors, "Currency has not been set.")
        return errors

    def _check_vat(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        if (
            values.get("customer")
            and values.get("customer").get("vat")
            and values.get("customer").get("countryCode")
            and values.get("customer").get("typeClient")
        ):
            country_id = self.get_country(values.get("customer").get("countryCode"))
            if (
                country_id
                and self.env["res.partner"]._run_vat_test(
                    values.get("customer").get("vat"),
                    country_id,
                    values.get("customer").get("typeClient") == "business",
                )
                is False
            ):
                errors = self._write_errors(errors, "Wrong VAT")
        return errors

    def _check_invoice_province(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        """
        errors = self._check_province_in_country(errors, values)
        return errors

    def _check_values(self, errors, values, company, ecommerce_connection_id):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with values to be checked
        :param company: res.company record of the current company
        """
        errors = self._check_company(errors, values)
        errors = self._check_payments(errors, values)
        errors = self._check_shipments(errors, values)
        errors = self._check_customer_country_province(errors, values)
        errors = self._check_shipping_country_province(errors, values)
        errors = self._check_billing_country_province(errors, values)
        errors = self._check_lang(errors, values)
        errors = self._check_currency(errors, values, company)
        if ecommerce_connection_id.check_customer_vat:
            errors = self._check_vat(errors, values)
        return errors

    def _check_invoice(self, values, move, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new invoice values
        :param move: account.move record with the newly created invoice
        :param errors: string with the current errors
        """
        if (
            float_compare(
                float(values.get("total")), move.amount_total, precision_digits=2
            )
            != 0
        ):
            errors = self._write_errors(
                errors,
                "Total in sales currency does not match the value sent with the call.",
            )
        if (
            float_compare(
                float(values.get("totalCompany")),
                move.amount_total_signed,
                precision_digits=2,
            )
            != 0
        ):
            errors = self._write_errors(
                errors,
                "Total in company currency does not match the value sent with "
                "the call.",
            )
        if (
            float_compare(
                float(values.get("taxTotal")), move.amount_tax, precision_digits=2
            )
            != 0
        ):
            errors = self._write_errors(
                errors,
                "Tax amount in sales currency does not match the value sent "
                "with the call.",
            )
        if (
            float_compare(
                float(values.get("taxTotalCompany")),
                move.amount_tax_signed,
                precision_digits=2,
            )
            != 0
        ):
            errors = self._write_errors(
                errors,
                "Tax amount in company currency does not match the value sent "
                "with the call.",
            )
        return errors

    def _check_invoice_lines(self, values, move, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new invoice lines values
        :param move: account.move record with the newly created invoice
        :param errors: string with the current errors
        """
        for line in values.get("lines"):
            invoice_line = move.invoice_line_ids.filtered(
                lambda a, line=line: a.ecommerce_id == int(line.get("id"))
            )
            if (
                float_compare(
                    float(line.get("total")),
                    invoice_line.price_total,
                    precision_digits=2,
                )
                != 0
            ):
                errors = self._write_errors(
                    errors,
                    "Total in sales currency in line with ID %s does not match "
                    "the value sent with the call." % line.get("id"),
                )
            if (
                float_compare(
                    float(line.get("subtotal")),
                    invoice_line.price_subtotal,
                    precision_digits=2,
                )
                != 0
            ):
                errors = self._write_errors(
                    errors,
                    "Subtotal in sales currency in line with ID %s does not "
                    "match the value sent with the call." % line.get("id"),
                )
        return errors

    def _check_shipping_lines(self, values, move, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new invoice lines values
        :param move: account.move record with the newly created invoice
        :param errors: string with the current errors
        """
        if values.get("shipments"):
            for line in values.get("shipments"):
                shipping_line = move.invoice_line_ids.filtered(
                    lambda a, line=line: a.ecommerce_shipping_id == int(line.get("id"))
                )
                tax_included = shipping_line.tax_ids[0].price_include
                compare_val = 0.0
                compare_field = ""
                if tax_included:
                    compare_val = shipping_line.price_total
                    compare_field = "Total"
                else:
                    compare_val = shipping_line.price_subtotal
                    compare_field = "Subtotal"
                if (
                    float_compare(
                        float(line.get("unitPrice")), compare_val, precision_digits=2
                    )
                    != 0
                ):
                    errors = self._write_errors(
                        errors,
                        "{} in sales currency in shipping line with ID {} does "
                        "not match the value sent with the call.".format(
                            compare_field, line.get("id")
                        ),
                    )
        return errors

    def _check_invoice_payments(self, values, move, errors):
        """Returns a string with the errors

        :param values: dictionary with the values to be used to compare to
            the new invoice payments
        :param move: account.move record with the newly created invoice
        :param errors: string with the current errors
        """
        payments = values.get("payments")
        if payments:
            payment_ids = move._get_reconciled_payments()
            if len(payments) != len(payment_ids):
                errors = self._write_errors(
                    errors, "The number of payments does not match."
                )
            for payment in payments:
                payment_id = payment_ids.filtered(
                    lambda a, payment=payment: a.ecommerce_payment_id
                    == int(payment.get("id"))
                )
                if not payment:
                    errors = self._write_errors(
                        errors,
                        "Payment with ID %s could not be found." % payment.get("id"),
                    )
                elif (
                    payment_id
                    and float_compare(
                        float(payment_id.amount_signed),
                        float(payment.get("unitPrice")),
                        precision_digits=2,
                    )
                    != 0
                ):
                    errors = self._write_errors(
                        errors,
                        "Amount in invoice currency for payment with ID {} does"
                        " not match.".format(payment.get("id")),
                    )
        if errors:
            errors = self._write_errors(
                errors,
                "PAYMENTS WERE DELETED AND INVOICE %s SENT TO DRAFT STATE" % move.name,
            )
        return errors

    def _check_mandatory_fields_credit_note(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with the values to be checked
        """
        if not values.get("companyId"):
            errors = self._write_errors(errors, "Company is missing.")
        if not values.get("origin"):
            errors = self._write_errors(errors, "Origin is missing.")
        if not values.get("return_type") not in ["total", "partial"]:
            errors = self._write_errors(errors, "Return type is missing or incorrect.")
        if not values.get("invoice_id"):
            errors = self._write_errors(errors, "Invoice ID is missing.")
        if values.get("return_type") == "partial" and not values.get("lines"):
            errors = self._write_errors(errors, "Lines are missing.")
        if not values.get("total"):
            errors = self._write_errors(errors, "Total is missing.")
        if not values.get("totalCompany"):
            errors = self._write_errors(errors, "Total company is missing.")
        if values.get("return_type") == "partial":
            if any(
                not line.get("productId")
                or not line.get("quantity")
                or not line.get("unitPrice")
                or not line.get("unitPriceCompany")
                or not line.get("unitPriceCompany")
                for line in values.get("lines")
            ):
                errors = self._write_errors(
                    errors,
                    "Product id, quantity, unit price and unit price company "
                    "are mandatory for all lines.",
                )
        return errors

    def _check_credit_notes_values(self, errors, values):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param values: dictionary with the values to be checked
        """
        errors = self._check_company(errors, values)
        return errors

    def _check_credit_lines(self, errors, invoice_id, lines, ecommerce_connection):
        """Returns a string with the errors

        :param errors: string with the current errors
        :param invoice_id: account.move with the newly created credit note
        :lines lines: list of dictionaries with the values of the credit note
            lines to compare
        :param ecommerce_connection: ecommerce.connection record
        """
        for line in lines:
            product_id = self._find_product(line, ecommerce_connection)
            product_lines_qty = sum(
                invoice_id.invoice_line_ids.filtered(
                    lambda a, product=product_id: a.product_id == product
                ).mapped("quantity")
            )
            if float(line.get("quantity")) > product_lines_qty:
                errors = self._write_errors(
                    errors,
                    "Quantity of product with Ecommerce ID {} is higher than "
                    "the quantity of product in the invoice.".format(
                        line.get("productId")
                    ),
                )
            return errors

    def _check_invoice_shipping_lines(self, values, move, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new invoice shipping lines values
        :param move: account.move record with the newly created invoice
        :param errors: string with the current errors
        """
        if values.get("shipments"):
            for line in values.get("shipments"):
                shipping_line = move.invoice_line_ids.filtered(
                    lambda a, line=line: a.ecommerce_shipping_id == int(line.get("id"))
                )
                if (
                    float_compare(
                        float(line.get("unitPrice")),
                        shipping_line.price_subtotal,
                        precision_digits=2,
                    )
                    != 0
                ):
                    errors = self._write_errors(
                        errors,
                        "Subtotal in sales currency in shipping line with ID "
                        "{} does not match the value sent with the call.".format(
                            line.get("id")
                        ),
                    )
        return errors

    def _check_sale_order(self, values, order, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new sale order values
        :param move: sale.order record with the newly created invoice
        :param errors: string with the current errors
        """
        if (
            float_compare(
                float(values.get("total")), order.amount_total, precision_digits=2
            )
            != 0
        ):
            errors = self._write_errors(
                errors,
                "Total in sales currency does not match the value sent with the call.",
            )
        if (
            float_compare(
                float(values.get("taxTotal")), order.amount_tax, precision_digits=2
            )
            != 0
        ):
            errors = self._write_errors(
                errors,
                "Tax amount in sales currency does not match the value sent "
                "with the call.",
            )
        return errors

    def _check_sale_lines(self, values, order, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new sale order lines values
        :param order: sale.order record with the newly created sale order
        :param errors: string with the current errors
        """
        for line in values.get("lines"):
            sale_order_line = order.order_line.filtered(
                lambda a, line=line: a.ecommerce_id == int(line.get("id"))
            )
            if (
                float_compare(
                    float(line.get("total")),
                    sale_order_line.price_total,
                    precision_digits=2,
                )
                != 0
            ):
                errors = self._write_errors(
                    errors,
                    "Total in sales currency in line with ID {} does not match"
                    " the value sent with the call.".format(line.get("id")),
                )
            if (
                float_compare(
                    float(line.get("subtotal")),
                    sale_order_line.price_subtotal,
                    precision_digits=2,
                )
                != 0
            ):
                errors = self._write_errors(
                    errors,
                    "Subtotal in sales currency in line with ID {} does not "
                    "match the value sent with the call.".format(line.get("id")),
                )
        return errors

    def _check_sale_shipping_lines(self, values, order, errors):
        """Returns a string with the errors

        :param values: dictionary with the valus to be used to compare to
            the new invoice shipping lines values
        :param move: account.move record with the newly created invoice
        :param errors: string with the current errors
        """
        if values.get("shipments"):
            for line in values.get("shipments"):
                shipping_line = order.order_line.filtered(
                    lambda a, line=line: a.ecommerce_shipping_id == int(line.get("id"))
                )
                if (
                    float_compare(
                        float(line.get("unitPrice")),
                        shipping_line.price_subtotal,
                        precision_digits=2,
                    )
                    != 0
                ):
                    errors = self._write_errors(
                        errors,
                        "Subtotal in sales currency in shipping line with ID "
                        "{} does not match the value sent with the call.".format(
                            line.get("id")
                        ),
                    )
        return errors

    def _invoice_address_values(self, values):
        """Returns a dictionary with the values for a new invoice address

        :param values: dictionary with the values of the new invoice address
        """
        name = values.get("billingAddress").get("firstname")
        if values.get("billingAddress").get("lastname"):
            name = "%s %s" % (name, values.get("billingAddress").get("lastname"))
        country_id = self.get_country(values.get("billingAddress").get("countryCode"))
        province_id = self.get_province(
            country_id, values.get("billingAddress").get("provinceCode")
        )
        return {
            "type": "invoice",
            "name": name,
            "country_id": country_id.id if country_id else False,
            "state_id": province_id.id if province_id else False,
            "street": values.get("billingAddress").get("street"),
            "street2": values.get("billingAddress").get("street2"),
            "city": values.get("billingAddress").get("city"),
            "zip": values.get("billingAddress").get("postcode"),
            "email": values.get("billingAddress").get("email"),
            "phone": values.get("billingAddress").get("phone"),
            "mobile": values.get("billingAddress").get("mobile"),
        }

    def _delivery_address_values(self, values):
        """Returns a dictionary with the values for a new shipping address

        :param values: dictionary with the values of the new shipping address
        """
        name = values.get("shippingAddress").get("firstname")
        if values.get("shippingAddress").get("lastname"):
            name = "%s %s" % (name, values.get("shippingAddress").get("lastname"))
        country_id = self.get_country(values.get("shippingAddress").get("countryCode"))
        province_id = self.get_province(
            country_id, values.get("shippingAddress").get("provinceCode")
        )
        return {
            "type": "delivery",
            "name": name,
            "country_id": country_id.id if country_id else False,
            "state_id": province_id.id if province_id else False,
            "street": values.get("shippingAddress").get("street"),
            "street2": values.get("shippingAddress").get("street2"),
            "city": values.get("shippingAddress").get("city"),
            "zip": values.get("shippingAddress").get("postcode"),
            "email": values.get("shippingAddress").get("email"),
            "phone": values.get("shippingAddress").get("phone"),
            "mobile": values.get("shippingAddress").get("mobile"),
        }

    def _create_connector_call(self, values, operation):
        """Returns a dictionary with the values for a new shipping address

        :param values: json values
        :param operation: whether 'invoice' or 'note'
        """
        return self.env["ecommerce.connector.call"].create(
            {
                "ecommerce_origin": values.get("origin"),
                "datetime": datetime.now(),
                "message_in": json.dumps(values, indent=4),
                "operation": operation,
            }
        )

    def _get_new_partner_vals(self, values, ecommerce_connection):
        """Returns a a dictionary with the values for the new partner

        :param values: dictionary with the values for the new partner
        :param ecommerce_connection: ecommerce.connection record
        """
        fiscal_position_type = (
            "b2c" if values.get("customer").get("typeClient") == "individual" else "b2b"
        )
        company_type = (
            "company"
            if values.get("customer").get("typeClient") == "business"
            else "person"
        )
        name = ""
        if company_type == "company":
            name = values.get("customer").get("comercialName")
        else:
            name = values.get("customer").get("firstname")
            if values.get("customer").get("lastname"):
                name = "%s %s" % (name, values.get("customer").get("lastname"))
        commercial_company_name = (
            values.get("customer").get("comercial_name")
            if values.get("customer").get("typeClient") == "business"
            else False
        )
        country_id = self.get_country(values.get("customer").get("countryCode"))
        province_id = self.get_province(
            country_id, values.get("customer").get("provinceCode")
        )
        vals = {
            "name": name,
            "commercial_company_name": commercial_company_name,
            "country_id": country_id.id if country_id else False,
            "state_id": province_id.id if province_id else False,
            "street": values.get("customer").get("street"),
            "street2": values.get("customer").get("street2"),
            "city": values.get("customer").get("city"),
            "zip": values.get("customer").get("postcode"),
            "vat": values.get("customer").get("vat"),
            "email": values.get("customer").get("email"),
            "company_type": company_type,
            "lang": values.get("customer").get("languageCode"),
            "fiscal_position_type": fiscal_position_type,
            "phone": values.get("customer").get("phone"),
            "mobile": values.get("customer").get("mobile"),
            "ecommerce_partner_ids": [
                (
                    0,
                    0,
                    {
                        "ecommerce_connection_id": ecommerce_connection.id,
                        "ecommerce_id": int(values.get("customer").get("id")),
                    },
                ),
            ],
        }
        if ecommerce_connection.create_contacts_single_company:
            vals["company_id"] = ecommerce_connection.company_id.id
        return vals

    def _create_new_partner(self, values, ecommerce_connection):
        """Returns a res.partner record with a newly created contact

        :param values: dictionary with the values for the new partner
        :param ecommerce_connection: ecommerce.connection record
        """
        vals = self._get_new_partner_vals(values, ecommerce_connection)
        partner = self.env["res.partner"].create(vals)
        return partner

    def _create_new_shipping_partner(self, values, partner, ecommerce_connection):
        """Returns a res.partner record with a newly created shipping contact

        :param values: dictionary with the values for the new partner
        :param partner: res.partner record of the parent contact
        :param ecommerce_connection: ecommerce.connection record
        """
        vals = self._delivery_address_values(values)
        vals["parent_id"] = partner.id
        if ecommerce_connection.create_contacts_single_company:
            vals["company_id"] = ecommerce_connection.company_id.id
        partner = self.env["res.partner"].create(vals)
        if values.get("shippingAddress").get("id"):
            self.env["ecommerce.partner"].create(
                {
                    "partner_id": partner.id,
                    "ecommerce_connection_id": ecommerce_connection.id,
                    "ecommerce_id": int(values.get("shippingAddress").get("id")),
                }
            )
        return partner

    def _create_new_invoice_partner(self, values, partner, ecommerce_connection):
        """Returns a res.partner record with a newly created invoice contact

        :param values: dictionary with the values for the new partner
        :param partner: res.partner record of the parent contact
        :param ecommerce_connection: ecommerce.connection record
        """
        vals = self._invoice_address_values(values)
        vals["parent_id"] = partner.id
        if ecommerce_connection.create_contacts_single_company:
            vals["company_id"] = ecommerce_connection.company_id.id
        if (
            not ecommerce_connection.duplicate_invoice_name
            and vals["name"].upper() == partner.name.upper()
        ):
            vals["name"] = ""
        partner = self.env["res.partner"].create(vals)
        if values.get("billingAddress").get("id"):
            self.env["ecommerce.partner"].create(
                {
                    "partner_id": partner.id,
                    "ecommerce_connection_id": ecommerce_connection.id,
                    "ecommerce_id": int(values.get("billingAddress").get("id")),
                }
            )
        return partner

    def _create_new_product(self, template, line, ecommerce_connection):
        """Returns a product.product record with a newly created product variant

        :param template: product.template record
        :param line: dictionary with the info of a sale line
        :param ecommerce_connection: ecommerce.connection record
        """
        attributes = self._manage_attributes(line.get("variants"))
        for a in attributes:
            product_template_attribute_line = self.env[
                "product.template.attribute.line"
            ].search(
                [
                    ("product_tmpl_id", "=", template.id),
                    ("attribute_id", "=", a.attribute_id.id),
                ],
                limit=1,
            )
            if (
                product_template_attribute_line
                and a.id not in product_template_attribute_line.value_ids.ids
            ):
                product_template_attribute_line.write({"value_ids": [(4, a.id)]})
            elif not product_template_attribute_line:
                template.write(
                    {
                        "attribute_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "attribute_id": a.attribute_id.id,
                                    "value_ids": [(4, a.id)],
                                },
                            )
                        ]
                    }
                )
        product_id = template.product_variant_id
        if template.product_variant_count > 1:
            product_id = template.product_variant_ids.filtered(
                lambda a: attributes
                == a.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id"
                )
            )
        if not self.env["ecommerce.product.product"].search(
            [
                ("product_id", "=", product_id.id),
                ("ecommerce_connection_id", "=", ecommerce_connection.id),
            ],
            limit=1,
        ):
            self.env["ecommerce.product.product"].create(
                {
                    "product_id": product_id.id,
                    "ecommerce_connection_id": ecommerce_connection.id,
                    "ecommerce_id": line.get("productId"),
                }
            )
        if product_id:
            product_vals = {}
            if not product_id.default_code and line.get("productSku"):
                product_vals["default_code"] = line.get("productSku")
            if not product_id.barcode and line.get("productBarcode"):
                product_vals["barcode"] = line.get("productBarcode")
            if not product_id.standard_price and line.get("cost"):
                product_vals["standard_price"] = float(line.get("cost"))
            if line.get("image"):
                product_vals["image_1920"] = line.get("image")
            if not product_id.description and line.get("productDescription"):
                product_vals["description"] = line.get("productDescription")
            if product_vals:
                # We use with_company as standard_price is company dependent
                product_id.with_company(ecommerce_connection.company_id.id).write(
                    product_vals
                )
        return product_id

    def _get_tax_by_country(self, rate, country, company):
        """Returns an account.tax record of a given rate form a given country

        :param rate: float, rate of the tax
        :param country: res.country record
        :param company: res.company record of the current company
        """
        tax_id = False
        if country.code.upper() == "ES":
            if rate == 21.00:
                tax_id = self.env.ref(
                    "l10n_es.%s_account_tax_template_s_iva21b" % company.id
                )
            elif rate == 10.00:
                tax_id = self.env.ref(
                    "l10n_es.%s_account_tax_template_s_iva10b" % company.id
                )
            elif rate == 4.00:
                tax_id = self.env.ref(
                    "l10n_es.%s_account_tax_template_s_iva4b" % company.id
                )
        elif country.code.upper() == "FR":
            if rate == 20.00:
                tax_id = self.env.ref("l10n_fr.%s_tva_normale" % company.id)
            elif rate == 10.00:
                tax_id = self.env.ref("l10n_fr.%s_tva_intermediaire" % company.id)
            elif rate == 5.50:
                tax_id = self.env.ref("l10n_fr.%s_tva_reduite" % company.id)
            elif rate == 2.10:
                tax_id = self.env.ref("l10n_fr.%s_tva_super_reduite" % company.id)
        return tax_id

    def _find_product(self, line, ecommerce_connection):
        """Returns a product.product record if found

        :param line: dictionary with the info of a new sale line
        :param ecommerce_connection: ecommerce.connection record
        """
        product_id = False
        if ecommerce_connection.product_search_rule == "ecommerce_id":
            ecommerce_product_id = self.env["ecommerce.product.product"].search(
                [
                    ("ecommerce_connection_id", "=", ecommerce_connection.id),
                    ("ecommerce_id", "=", line.get("productId")),
                ],
                limit=1,
            )
            if ecommerce_product_id:
                product_id = ecommerce_product_id.product_id
        elif ecommerce_connection.product_search_rule == "sku":
            product_id = self.env["product.product"].search(
                [
                    ("default_code", "=", line.get("productSku")),
                    "|",
                    ("company_id", "=", ecommerce_connection.company_id.id),
                    ("company_id", "=", False),
                ]
            )
        elif ecommerce_connection.product_search_rule == "barcode":
            product_id = self.env["product.product"].search(
                [
                    ("barcode", "=", line.get("productBarcode")),
                    "|",
                    ("company_id", "=", ecommerce_connection.company_id.id),
                    ("company_id", "=", False),
                ]
            )
        return product_id

    def _create_new_product_template(self, line, company, ecommerce_connection):
        """Returns a product.template record of a newly created product

        :param line: dictionary with the info of a new sale line
        :param company: res.company record of the current company
        :param ecommerce_connection: ecommerce.connection record
        """
        tax_id = self._get_tax_by_country(
            line.get("productTaxCompany"), company.country_id, company
        )

        vals = {
            "name": line.get("productName"),
            "taxes_id": [(6, 0, [tax_id.id])],
            "type": line.get("productType"),
            "invoice_policy": "order",
        }
        if ecommerce_connection.create_products_single_company:
            vals["company_id"] = ecommerce_connection.company_id.id
        template = self.env["product.template"].create(vals)
        template.product_variant_id.write(
            {
                "default_code": line.get("productSku")
                if line.get("productSku")
                else False,
                "barcode": line.get("productBarcode")
                if line.get("productBarcode")
                else False,
            }
        )
        self.env["ecommerce.product.template"].create(
            {
                "product_template_id": template.id,
                "ecommerce_connection_id": ecommerce_connection.id,
                "ecommerce_id": line.get("productTemplateId"),
            }
        )
        self.env["ecommerce.product.product"].create(
            {
                "product_id": template.product_variant_id.id,
                "ecommerce_connection_id": ecommerce_connection.id,
                "ecommerce_id": line.get("productId"),
            }
        )
        return template

    def _create_products(self, errors, lines, ecommerce_connection):
        """Creates all the needed products and returns de found errors

        :param errors: string with the current errors
        :param lines: list of dictionaries with the info of all the new sale lines
        :param ecommerce_connection: ecommerce.connection record
        """
        company = ecommerce_connection.company_id
        for line in lines:
            product_id = self._find_product(line, ecommerce_connection)
            # Check if another product with the same barcode is in the system
            if not product_id:
                if line.get("productBarcode") and self.env["product.product"].search(
                    [("barcode", "=", line.get("productBarcode"))]
                ):
                    errors = self._write_errors(
                        errors,
                        "Product with barcode %s already in the system."
                        % line.get("productBarcode"),
                    )
                if not errors:
                    product_template_id = False
                    ecommerce_product_template = self.env[
                        "ecommerce.product.template"
                    ].search(
                        [
                            ("ecommerce_connection_id", "=", ecommerce_connection.id),
                            ("ecommerce_id", "=", line.get("productTemplateId")),
                        ],
                        limit=1,
                    )
                    if ecommerce_product_template:
                        product_template_id = (
                            ecommerce_product_template.product_template_id
                        )
                    if not product_template_id:
                        product_template_id = self._create_new_product_template(
                            line, company, ecommerce_connection
                        )
                    if line.get("variants"):
                        self._create_new_product(
                            product_template_id, line, ecommerce_connection
                        )
            elif company.id not in product_id.taxes_id.mapped("company_id").ids:
                self._add_company_taxes(product_id.product_tmpl_id, line, company)
        return errors

    def _create_payments(self, moves, values):
        """Creates the payments

        :param moves: account.move record with the newly created invoice
        :param values: dictionary with the info of the new sale
        """
        for payment in values.get("payments"):
            payment_mode_id = self.env["account.payment.mode"].search(
                [
                    ("name", "=ilike", payment.get("method")),
                    ("company_id", "=", int(values.get("companyId"))),
                ],
                limit=1,
            )
            wizard = (
                self.env["account.payment.register"]
                .with_context(active_ids=moves.ids, active_model="account.move")
                .create(
                    {
                        "payment_date": moves[0].date,
                        "amount": payment.get("unitPrice"),
                        "currency_id": moves[0].currency_id.id,
                        "journal_id": payment_mode_id.fixed_journal_id.id,
                    }
                )
            )
            move_payment = wizard._create_payments()
            if move_payment:
                move_payment.write({"ecommerce_payment_id": payment.get("id")})

    def _manage_attributes(self, variants):
        """Returns a recordset of product.attribute.value

        :param variants: dictionary attribute_name: value
        """
        attribute_ids = self.env["product.attribute.value"]
        for v in variants:
            product_attribute_id = self.env["product.attribute"].search(
                [("name", "=ilike", v)], limit=1
            )
            if not product_attribute_id:
                product_attribute_id = self.env["product.attribute"].create({"name": v})
            attribute_value_id = product_attribute_id.value_ids.filtered(
                lambda a, v=v: a.name == variants.get(v)
            )
            if not attribute_value_id:
                attribute_value_id = self.env["product.attribute.value"].create(
                    {"attribute_id": product_attribute_id.id, "name": variants.get(v)}
                )
            attribute_ids += attribute_value_id[0]
        return attribute_ids

    def _add_company_taxes(self, product_template, line, company):
        """Adds a sale tax to a product template

        :param product_template: product.template record
        :param line: ditionary with line info
        :param company: res.company record of the current company
        """
        tax_id = self._get_tax_by_country(
            line.get("productTaxCompany"), company.country_id, company
        )
        if tax_id:
            product_template.write({"taxes_id": [(4, tax_id.id)]})

    def _update_currency_exchange_rate(self, exchange_rate, currency_id, company):
        """Updates or create new exchange rate

        :param exchange_rate: float with the exchange rate
        :param currency_id: res.currency record to add an exchange rate to
        :param company: res.company record of the current company
        """
        if currency_id != company.currency_id:
            if currency_id.rate_ids and currency_id.rate_ids.filtered(
                lambda a: a.name == fields.Date.today() and a.company_id == company
            ):
                rate = currency_id.rate_ids.filtered(
                    lambda a: a.name == fields.Date.today()
                )
                rate[0].write({"inverse_company_rate": float(exchange_rate)})
            else:
                self.env["res.currency.rate"].create(
                    {
                        "name": fields.Date.today(),
                        "currency_id": currency_id.id,
                        "inverse_company_rate": exchange_rate,
                        "company_id": company.id,
                    }
                )

    def _create_sale(
        self,
        connector_call,
        values,
        errors,
        ecommerce_connection=False,
        payment_errors=False,
        order_id=False,
        move_id=False,
    ):
        if not errors and not payment_errors:
            file = False
            if move_id:
                file = self.env.ref("account.account_invoices")._render_qweb_pdf(
                    move_id.id
                )[0]
            else:
                file = self.env.ref("sale.action_report_saleorder")._render_qweb_pdf(
                    order_id.id
                )[0]
            file = base64_bytes = b64encode(file)
            file = base64_bytes.decode("utf-8")
            connector_call.write(
                {
                    "state": "done",
                    "sale_order_id": order_id.id,
                    "account_move_id": move_id.id if move_id else False,
                }
            )
            vals = {
                "status": "OK",
                "result": {
                    "sale_id": order_id.id,
                    "invoice_id": move_id.id if move_id else False,
                    "ecommerce_id": values.get("id"),
                    "pdf": file,
                },
            }
        elif payment_errors:
            if move_id:
                move_id.button_draft()
                move_id[0]._get_reconciled_payments().unlink()
            vals = {
                "status": "error",
                "error_message": payment_errors,
                "ecommerce_id": values.get("id"),
            }
            connector_call.write(
                {
                    "state": "error",
                    "error": payment_errors,
                    "sale_order_id": order_id.id,
                    "account_move_id": move_id.id if move_id else False,
                }
            )
        else:
            vals = {
                "status": "error",
                "error_message": errors,
                "ecommerce_id": values.get("id"),
            }
            connector_call.write(
                {
                    "state": "error",
                    "error": errors,
                }
            )
        connector_call.write(
            {
                "message_out": json.dumps(vals, indent=4),
                "ecommerce_connection_id": ecommerce_connection.id
                if ecommerce_connection
                else False,
            }
        )
        return vals

    def _get_additional_order_vals(self, values, ecommerce_connection):
        """To be extended by other modules so additional values can be set
        for the sale order

        :param values: dictionary with the info of the new sale
        :param ecommerce_connection: ecommerce.connection instance
        """
        return {}

    def _get_order_vals(
        self, values, ecommerce_connection, company, connector_call, number, errors
    ):
        vals = {}
        partner_id = self._get_contact(values, ecommerce_connection)
        shipping_address_id = self._get_shipping_contact(
            partner_id, values, ecommerce_connection
        )
        invoice_address_id = self._get_invoice_contact(
            partner_id, values, ecommerce_connection
        )
        currency_id = self.env["res.currency"].search(
            [("name", "=", values.get("currencyCode"))], limit=1
        )
        self._update_currency_exchange_rate(
            values.get("exchangeRate"), currency_id, company
        )
        pricelist_id = False
        if currency_id:
            pricelist_id = self.env["product.pricelist"].search(
                [
                    ("ecommerce_connector_default_currency", "=", True),
                    ("currency_id", "=", currency_id.id),
                ],
                limit=1,
            )
        if not pricelist_id:
            pricelist_id = self.env.ref("product.list0")
        errors = self._create_products(
            errors, values.get("lines"), ecommerce_connection
        )
        if errors:
            return self._create_sale(
                connector_call, values, errors, ecommerce_connection
            )
        fiscal_position_id = self._get_fiscal_position(
            company.country_id, shipping_address_id, values, company
        )
        if ecommerce_connection.use_odoo_so_sequence:
            vals["client_order_ref"] = number
        else:
            vals["name"] = number
        vals.update(
            {
                "ecommerce_id": values.get("id"),
                "pricelist_id": pricelist_id.id,
                "partner_id": partner_id.id,
                "partner_shipping_id": shipping_address_id.id,
                "partner_invoice_id": invoice_address_id.id,
                "fiscal_position_id": fiscal_position_id.id,
                "note": values.get("notes"),
                "origin": values.get("origin"),
                "order_line": self._get_order_lines(
                    fiscal_position_id, values, ecommerce_connection
                ),
                "date_order": values.get("dateOrder"),
                "ecommerce_connector_id": ecommerce_connection.id,
            }
        )
        if ecommerce_connection.invoice_policy:
            vals["invoice_policy"] = ecommerce_connection.invoice_policy
        if values.get("payments"):
            payment_mode_id = self.env["account.payment.mode"].search(
                [
                    ("name", "=ilike", values.get("payments")[0].get("method")),
                    ("company_id", "=", int(values.get("companyId"))),
                ],
                limit=1,
            )
            if payment_mode_id:
                vals.update({"payment_mode_id": payment_mode_id.id})
        delivery_carrier = False
        if values.get("shipments"):
            delivery_carrier = self.env["delivery.carrier"].search(
                [("name", "=ilike", values.get("shipments")[0].get("method"))], limit=1
            )
        vals["carrier_id"] = delivery_carrier and delivery_carrier.id
        vals.update(self._get_additional_order_vals(values, ecommerce_connection))
        return vals

    @api.model
    def external_create_sale(self, values):
        connector_call = self._create_connector_call(values, "invoice")
        errors = ""
        payment_errors = ""
        company = int(values.get("companyId"))
        company_id = self.env["res.company"].search([("id", "=", company)])
        if not company_id:
            errors = self._write_errors(errors, "Company not found.")
            return self._create_sale(connector_call, values, errors)
        if not company_id.accept_ecommerce_connector:
            errors = self._write_errors(
                errors, "The company does not accept the external call."
            )
            return self._create_sale(connector_call, values, errors)
        if errors:
            return self._create_sale(connector_call, values, errors)

        ecommerce_connection_id = self.env["ecommerce.connection"].search(
            [
                ("ecommerce_id", "=", int(values.get("ecommerceId"))),
                ("company_id", "=", company_id.id),
            ],
            limit=1,
        )
        if not ecommerce_connection_id:
            errors = self._write_errors(errors, "Ecommerce Connection not found.")
            return self._create_sale(
                connector_call, values, errors, ecommerce_connection_id
            )

        # Put lang in context
        self = self.with_context(lang=ecommerce_connection_id.lang)

        errors = self._check_mandatory_fields(
            errors, values, company_id, ecommerce_connection_id
        )
        number = values.get("number")
        if self.env["sale.order"].search(
            [
                ("ecommerce_id", "=", int(values.get("id"))),
                ("company_id", "=", company_id.id),
                ("state", "!=", "cancel"),
            ],
            limit=1,
        ):
            errors = self._write_errors(
                errors,
                "Sale {} (id {}) is already imported.".format(number, values.get("id")),
            )
            return self._create_sale(
                connector_call, values, errors, ecommerce_connection_id
            )

        order_id = False
        move_id = False
        errors = self._check_has_country(errors, company_id)
        if errors:
            return self._create_sale(
                connector_call, values, errors, ecommerce_connection_id
            )

        errors = self._check_values(errors, values, company_id, ecommerce_connection_id)
        if errors:
            return self._create_sale(
                connector_call, values, errors, ecommerce_connection_id
            )

        order_vals = self._get_order_vals(
            values, ecommerce_connection_id, company_id, connector_call, number, errors
        )

        order_id = self.env["sale.order"].with_company(company).create(order_vals)
        order_id.flush()
        order_id.action_confirm()
        if ecommerce_connection_id.create_invoice:
            moves = order_id.with_company(company)._create_invoices()
            if moves:
                moves.write({"ecommerce_id": order_id.ecommerce_id})
            errors = self._check_invoice(values, moves[0], errors)
            errors = self._check_invoice_lines(values, moves[0], errors)
            errors = self._check_invoice_shipping_lines(values, moves[0], errors)
            if errors:
                moves.unlink()
                order_id.action_cancel()
                order_id.unlink()
            elif ecommerce_connection_id.validate_invoice:
                moves.with_company(company).action_post()
                move_id = moves[0]
                self._create_payments(moves, values)
                payment_errors = self._check_invoice_payments(
                    values, move_id, payment_errors
                )
        else:
            errors = self._check_sale_order(values, order_id, errors)
            errors = self._check_sale_lines(values, order_id, errors)
            errors = self._check_sale_shipping_lines(values, order_id, errors)
            if errors:
                order_id.action_cancel()
                order_id.unlink()

        return self._create_sale(
            connector_call,
            values,
            errors,
            ecommerce_connection_id,
            payment_errors,
            order_id,
            move_id,
        )

    @api.model
    def external_create_credit_note(self, values):
        self._create_connector_call(values, "credit")
        vals = False
        errors = ""
        credit_note = False
        if not errors:
            errors = self._check_credit_notes_values(errors, values)
            file = False
            if not errors:
                company = int(values.get("companyId"))
                ecommerce_connection = values.get("ecommerceId")
                if not ecommerce_connection:
                    errors = self._write_errors(
                        errors, "Ecommerce Connection is missing."
                    )
                if not errors:
                    invoice_id = (
                        self.env["account.move"]
                        .with_company(company)
                        .search(
                            [
                                ("ecommerce_id", "=", int(values.get("invoiceId"))),
                                (
                                    "ecommerce_connector_id",
                                    "=",
                                    int(ecommerce_connection),
                                ),
                            ]
                        )
                    )
                    if not invoice_id:
                        errors = self._write_errors(errors, "Credit note not found.")
                    if not errors:
                        refund_method = (
                            "cancel"
                            if values.get("returnType") == "total"
                            else "refund"
                        )
                        refund_invoice_wizard = (
                            self.env["account.move.reversal"]
                            .with_context(
                                **{
                                    "active_ids": [invoice_id.id],
                                    "active_id": invoice_id.id,
                                    "active_model": "account.move",
                                }
                            )
                            .create(
                                {
                                    "refund_method": refund_method,
                                    "reason": "refund",
                                    "journal_id": invoice_id.journal_id.id,
                                }
                            )
                        )
                        credit_note_action = refund_invoice_wizard.reverse_moves()
                        credit_note = self.env["account.move"].browse(
                            credit_note_action.get("res_id")
                        )
                        if refund_method == "refund":
                            ecommerce_connection_id = self.env[
                                "ecommerce.connection"
                            ].search(
                                [
                                    (
                                        "ecommerce_id",
                                        "=",
                                        int(values.get("ecommerceId")),
                                    ),
                                    ("company_id", "=", company),
                                ],
                                limit=1,
                            )
                            if not ecommerce_connection_id:
                                errors = self._write_errors(
                                    errors, "Ecommerce Connection not found."
                                )
                            if not errors:
                                errors = self._check_credit_lines(
                                    errors,
                                    invoice_id,
                                    values.get("lines"),
                                    ecommerce_connection_id,
                                )
                                if not errors:
                                    credit_note.write({"invoice_line_ids": False})
                                    invoice_lines = self._get_credit_note_lines(
                                        values.get("lines"),
                                        ecommerce_connection_id,
                                    )
                                    credit_note.write(
                                        {"invoice_line_ids": invoice_lines}
                                    )
                                    credit_note.action_post()
                        if not errors:
                            file = self.env.ref(
                                "account.account_invoices"
                            )._render_qweb_pdf(credit_note.id)[0]
                            base64_bytes = b64encode(file)
                            file = base64_bytes.decode("utf-8")
                            vals = {
                                "status": "OK",
                                "result": {
                                    "credit_note_id": credit_note.id,
                                    "pdf": file,
                                },
                            }
        if errors:
            if credit_note:
                credit_note.unlink()
            vals = {"status": "error", "error_message": errors}
        return vals
