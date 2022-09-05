# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import datetime
from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductManagementConnector(models.Model):
    _name = "product.management.connector"
    _description = "Product Management Connector"

    def _write_errors(self, errors, new_error):
        """ Returns errors string after adding a new error

            :param errors: string with current errors
            :param new_error: string with new error to be added
            :param mode: 'rp' for receivable/payable or 'other'
        """
        return "%s%s\n" % (errors, new_error)

    def _check_create_mandatory_fields(self, errors, values, company, ecommerce_connection):
        """ Returns a string with the errors

            :param errors: string with the current errors
            :param values: dictionary with the values to be checked
            :param company: res.company record
            :param ecommerce_connection: ecommerce.connection record
        """
        if not values.get('productName'):
            errors = self._write_errors(
                errors,
                "Product name in product not provided."
            )
        if not values.get('productTemplateId'):
            errors = self._write_errors(
                errors,
                "Product template ID in product not provided."
            )
        if not values.get('productId'):
            errors = self._write_errors(
                errors,
                "Product ID in product not provided."
            )
        if not values.get('productTaxCompany'):
            errors = self._write_errors(
                errors,
                "Product tax in product not provided."
            )
        if not values.get('productType'):
            errors = self._write_errors(
                errors,
                "Product type in product not provided."
            )
        return errors

    def _check_update_mandatory_fields(self, errors, values, company, ecommerce_connection):
        """ Returns a string with the errors

            :param errors: string with the current errors
            :param values: dictionary with the values to be checked
            :param company: res.company record
            :param ecommerce_connection: ecommerce.connection record
        """
        if ecommerce_connection.product_search_rule == 'ecommerce_id' and not values.get('productId'):
            errors = self._write_errors(
                errors,
                "Product ID in product not provided."
            )                    
        if ecommerce_connection.product_search_rule == 'sku' and not values.get('productSku'):
            errors = self._write_errors(
                errors,
                "Product SKU in product not provided."
            )
        if ecommerce_connection.product_search_rule == 'barcode' and not values.get('productBarcode'):
            errors = self._write_errors(
                errors,
                "Product barcode in product not provided."
            )    
        return errors

    def _get_product_template(self, product_vals, company, ecommerce_connection):
        """ Returns a product.template record

            :param errors: string with the current errors
            :param values: dictionary with the values to be checked
            :param company: res.company record
            :param ecommerce_connection: ecommerce.connection record
        """
        product_template = False
        ecommerce_product_template = self.env['ecommerce.product.template'].search([
            ('ecommerce_connection_id', '=', ecommerce_connection.id),
            ('ecommerce_id', '=', product_vals.get('productTemplateId'))
        ], limit=1)
        if not ecommerce_product_template:
            product_template = self.env['ecommerce.connector']._create_new_product_template(
                product_vals, company, ecommerce_connection
            )
        else:
            product_template = ecommerce_product_template.product_template_id
        return product_template

    def _check_connection_values(self, values, errors):
        """ Returns a string with errors
            Returns a ecommerce.connection record
            Returns a res.company record

            :param values: dictionary with the values to be checked
            :param errors: string with errors
        """
        errors = ""
        ecommerce_connection = False
        company_id = values.get('companyId')
        company = self.env['res.company'].search([
            ('id', '=', company_id)
        ])
        if not company_id:
            errors = self._write_errors(errors, "Company not provided.")
        elif not company:
            errors = self._write_errors(errors, "Company not found.")
        elif not company.accept_product_management_connector:
            errors = self._write_errors(errors, "Company does not accept the external call.")
        elif not values.get('ecommerceId'):
            errors = self._write_errors(errors, "Ecommerce ID not provided.")
        elif values.get('ecommerceId'):
            ecommerce_connection = self.env['ecommerce.connection'].search([
                ('ecommerce_id', '=', int(values.get('ecommerceId'))),
                ('company_id', '=', company.id)
            ], limit=1)
            if not ecommerce_connection:
                errors = self._write_errors(errors, "Ecommerce Connection not found.")
        return errors, ecommerce_connection, company

    def _get_update_vals(self, values, ecommerce_connection, company):
        """ Returns a dictionary with product.product values to be updated

            :param values: dictionary with the product values
            :param ecommerce_connection: ecommerce.connection record
            :param company: res.company record
        """
        vals = {}
        if values.get('productSku'):
            vals['default_code'] = values.get('productSku')
        if values.get('productBarcode'):
            vals['barcode'] = values.get('productBarcode')
        if values.get('productDescription'):
            vals['description'] = values.get('productDescription')
        if values.get('productName'):
            vals['name'] = values.get('productName')
        if values.get('image'):
            vals['image_1920'] = values.get('image')
        if values.get('cost'):
            vals['standard_price'] = values.get('cost')
        if 'saleOk' in values:
            vals['sale_ok'] = values.get('saleOk')
        if values.get('productDescription'):
            vals['description'] = values.get('productDescription')
        if ecommerce_connection.product_search_rule == 'sku' and vals.get('sku'):
            del vals['default_code']
        elif ecommerce_connection.product_search_rule == 'barcode' and vals.get('barcode'):
            del vals['barcode']
        return vals

    def _update_additional_fields(self, values, company, product, errors):
        """ Returns a string with errors
            Inherit to write additional fields in product

            :param values: dictionary with the product values
            :param company: res.company record
            :param product: product.product record
            :param errors; string with found errors
        """
        # Update Taxes
        if values.get('productTaxCompany'):
            tax_id = self.env['ecommerce.connector']._get_tax_by_country(
                values.get('productTaxCompany'),
                company.country_id,
                company
            )
            if not tax_id:
                errors = self._write_errors(
                    errors,
                    'Taxes not found'
                )
            if not errors:
                current_taxes = product.taxes_id.filtered(
                    lambda a: a.company_id.id == int(values.get('companyId'))
                )
                for tax in current_taxes:
                    product.write({
                        'taxes_id': [(3, tax.id)]
                    })
                if tax_id:
                    product.write({
                        'taxes_id': [(4, tax_id.id)],
                    })
        return errors

    def _create_answer(self, errors, values, operation, ecommerce_connection):
        connector_call = self.env['ecommerce.connector.call'].create({
            'datetime': datetime.now(),
            'message_in': json.dumps(values, indent=4),
            'operation': operation,
            'ecommerce_connection_id': ecommerce_connection.id if ecommerce_connection else False,
        })
        if errors:
            vals = {
                'status': 'error',
                'error_message': errors
            }
            connector_call.write({
                'state': 'error',
                'error': errors,
            })
            _logger.error("Products could not be created/updated.")
        else:
            vals = {
                'status': 'OK',
                'result': 'product created/updated'
            }
            connector_call.write({
                'state': 'done'
            })
        connector_call.write({
            'message_out': json.dumps(vals)
        })
        return json.dumps(vals)

    @api.model
    def external_create_product(self, values):
        errors = ''
        errors, ecommerce_connection, company = self._check_connection_values(values, errors)
        if errors:
            return self._create_answer(errors, values, 'create_product', ecommerce_connection)          
        errors = self._check_create_mandatory_fields(errors, values, company, ecommerce_connection)
        if errors:
            return self._create_answer(errors, values, 'create_product', ecommerce_connection)

        product_template = self._get_product_template(values, company, ecommerce_connection)
        if values.get('variants'):
            product = self.env['ecommerce.connector']._create_new_product(
                product_template, values, ecommerce_connection
            )
            _logger.info('Product with ID {} created.'.format(product.id))
        return self._create_answer(errors, values, 'create_product', ecommerce_connection)

    @api.model
    def external_update_product(self, values):
        errors = ''
        errors, ecommerce_connection, company = self._check_connection_values(values, errors)
        if errors:
            return self._create_answer(errors, values, 'update_product', ecommerce_connection)
        errors = self._check_update_mandatory_fields(errors, values, company, ecommerce_connection)
        if errors:
            return self._create_answer(errors, values, 'update_product', ecommerce_connection)

        product = self.env['ecommerce.connector']._find_product(values, ecommerce_connection)
        if not product:
            errors = self._write_errors(
                errors,
                "Product not found."
            )
            return self._create_answer(errors, values, 'update_product', ecommerce_connection)
        # We use with_company as standard_price is company dependent.
        product.with_company(company).with_context(lang=ecommerce_connection.lang).write(
            self._get_update_vals(values, ecommerce_connection, company)
        )
        errors = self._update_additional_fields(values, company, product, errors)
        _logger.info('Product with ID {} updated.'.format(product.id))
        return self._create_answer(errors, values, 'update_product', ecommerce_connection)
