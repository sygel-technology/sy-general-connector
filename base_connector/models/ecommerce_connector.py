# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from base64 import b64encode
from datetime import datetime

from odoo import api, models


class EcommerceConnector(models.Model):
    _name = "ecommerce.connector"
    _description = "Ecommerce Connector"

    def _write_errors(self, errors, new_error):
        """Returns errors string after adding a new error

        :param errors: string with current errors
        :param new_error: string with new error to be added
        """
        return f"{errors}{new_error}\n"

    @api.model
    def _get_company(self, values):
        company = int(values.get("companyId"))
        company_id = self.env["res.company"].search([("id", "=", company)])
        error = False
        if not company_id:
            error = "Company not found."
        elif not company_id.accept_ecommerce_connector:
            error = "The company does not accept the external call."
        return company_id, error

    @api.model
    def _get_ecommerce_connection(self, values, company_id):
        ecommerce_connection = self.env["ecommerce.connection"].search(
            [
                ("ecommerce_id", "=", int(values.get("ecommerceId"))),
                ("company_id", "=", company_id.id),
            ],
            limit=1,
        )
        error = False
        if not ecommerce_connection:
            error = "Ecommerce Connection not found."
        return ecommerce_connection, error

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
                    domain = [("id", "=", ecommerce_partner_id.partner_id.id)]
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
                values.get("shippingAddress", {}).get("countryCode")
                or values.get("customer").get("countryCode")
            )
            if country_id:
                if vat.startswith(country_id.code):
                    vat_with_code = vat
                    vat = vat[len(country_id.code) :]
                else:
                    vat_with_code = f"{country_id.code}{vat}"
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
                    name = f"{name} {values.get('customer').get('lastname')}"
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
        if ecommerce_connection.update_contacts and partner_id:
            self._update_partner(partner_id, values, ecommerce_connection)
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

    def _check_customer_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection, excluded_fields=False
    ):
        if not excluded_fields:
            excluded_fields = []
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
        if not excluded_fields:
            excluded_fields = []
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
        if not excluded_fields:
            excluded_fields = []
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

    def _check_billing_address_search_mandatory_fields(
        self, errors, values, company_id, ecommerce_connection
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
        self, errors, values, company_id, ecommerce_connection
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

    def _create_connector_call(self, values, scope, operation):
        """Returns a dictionary with the values for a new shipping address

        :param values: json values
        :param operation: whether 'invoice' or 'note'
        """
        return self.env["ecommerce.connector.call"].create(
            {
                "ecommerce_origin": values.get("origin"),
                "datetime": datetime.now(),
                "message_in": json.dumps(values, indent=4),
                "scope": scope,
                "operation": operation,
            }
        )

    def _get_new_partner_vals(self, values, ecommerce_connection):
        """Returns a a dictionary with the values for the new partner

        :param values: dictionary with the values for the new partner
        :param ecommerce_connection: ecommerce.connection record
        """
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
                name = f"{name} {values.get('customer').get('lastname')}"
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

    def _update_partner(
        self, partner, values, ecommerce_connection, precalculated_values=None
    ):
        """Sets in a res.partner record the new values sent from the ecommerce

        :param partner: single partner to update
        :param values: dictionary with the values for the new partner
        :param ecommerce_connection: ecommerce.connection record
        """
        partner.ensure_one()
        if precalculated_values is None:
            vals = self._get_new_partner_vals(values, ecommerce_connection)
        else:
            vals = precalculated_values
        vals.pop("ecommerce_partner_ids", False)
        return partner.write(vals)

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

    def _invoice_address_values(self, values):
        """Returns a dictionary with the values for a new invoice address

        :param values: dictionary with the values of the new invoice address
        """
        name = values.get("billingAddress").get("firstname")
        if values.get("billingAddress").get("lastname"):
            name = f"{name} {values.get('billingAddress').get('lastname')}"
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
            name = f"{name} {values.get('shippingAddress').get('lastname')}"
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

    def _get_external_partner_vals(self, partner_id):
        """Returns a dictionary with the values of an external partner id
        Inverse function of _get_new_partner_vals

        :param partner_id: the partner record to convert
        """
        partner_id.ensure_one()
        return {
            "id": partner_id.ecommerce_partner_ids[0].id,
            "name": partner_id.name,
            "comercialName": partner_id.commercial_company_name
            if partner_id.company_type == "company"
            else partner_id.name,
            "countryCode": partner_id.country_id.code,
            "provinceCode": partner_id.state_id.code,
            "street": partner_id.street,
            "street2": partner_id.street2,
            "city": partner_id.city,
            "postcode": partner_id.zip,
            "vat": partner_id.vat,
            "email": partner_id.email,
            "typeClient": "business"
            if partner_id.company_type == "company"
            else "individual",
            "languageCode": partner_id.lang,
            "phone": partner_id.phone,
            "mobile": partner_id.mobile,
        }

    def _create_response(
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
                file = self.env["ir.actions.report"]._render_qweb_pdf(
                    "account.account_invoices", res_ids=move_id.id
                )[0]
            else:
                file = self.env["ir.actions.report"]._render_qweb_pdf(
                    "sale.action_report_saleorder", res_ids=order_id.id
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
                    "ecommerce_id": values.get("ecommerceId"),
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
                "ecommerce_id": values.get("ecommerceId"),
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
                "ecommerce_id": values.get("ecommerceId"),
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

    @api.model
    def external_update_customer(self, values):
        connector_call = self._create_connector_call(values, "base", "update_contact")
        company, error = self._get_company(values)
        if not error:
            ecommerce_connection, error = self._get_ecommerce_connection(
                values, company
            )
        if not error:
            domain = self._get_contact_domain(values, ecommerce_connection)
            if not domain:
                error = "The partner was not found"
        if not error:
            partner_id = self.env["res.partner"].search(
                domain,
                limit=1,
            )
            if not partner_id:
                error = "The partner was not found"
            elif partner_id.filtered(lambda p: p.type in ["invoice", "delivery"]):
                error = "The partner cannot be a invoice or delivery address"
        if error:
            res = self._create_response(
                connector_call, values, error, ecommerce_connection
            )
        else:
            self._update_partner(partner_id, values, ecommerce_connection)
            connector_call.write(
                {
                    "state": "done",
                }
            )
            res = {"status": "OK"}
        return res

    @api.model
    def external_read_customer(self, values):
        connector_call = self._create_connector_call(
            values, "base", "external_read_customer"
        )
        company, error = self._get_company(values)
        if not error:
            ecommerce_connection, error = self._get_ecommerce_connection(
                values, company
            )
        if not error:
            domain = self._get_contact_domain(values, ecommerce_connection)
            if not domain:
                error = "The partner was not found"
        if not error:
            partner_id = self.env["res.partner"].search(
                domain,
                limit=1,
            )
            if not partner_id:
                error = "The partner was not found"
        if error:
            res = self._create_response(
                connector_call, values, error, ecommerce_connection
            )
        else:
            connector_call.write(
                {
                    "state": "done",
                }
            )
            res = {
                "status": "OK",
                "result": self._get_external_partner_vals(partner_id),
            }
        return res

    @api.model
    def external_create_customer(self, values):
        connector_call = self._create_connector_call(
            values, "base", "external_create_customer"
        )
        company, error = self._get_company(values)
        if not error:
            ecommerce_connection, error = self._get_ecommerce_connection(
                values, company
            )
        if not error:
            error = self._check_customer_mandatory_fields(
                error, values, company, ecommerce_connection, []
            )
        if not error:
            domain = self._get_contact_domain(values, ecommerce_connection)
            if domain:
                partner_id = self.env["res.partner"].search(
                    domain,
                    limit=1,
                )
                if partner_id:
                    error = "The partner is already created in the system"
        if error:
            res = self._create_response(connector_call, values, error)
        else:
            partner_id = self._create_new_partner(values, ecommerce_connection)
            connector_call.write(
                {
                    "state": "done",
                }
            )
            res = {
                "status": "OK",
                "result": {
                    "partner_id": partner_id.id,
                    "ecommerce_id": partner_id.ecommerce_partner_ids[:1].id,
                },
            }
        return res
