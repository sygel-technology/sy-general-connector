# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from datetime import datetime
from odoo import api, models


SEARCH_KEYS = [
    'odooId',
    'ecommerceId',
    'sku',
    'barcode'
]


class StockCheckConnector(models.Model):
    _name = "stock.check.connector"
    _description = "Stock Check Connector"

    def _write_errors(self, errors, new_error):
        """ Returns errors string after adding a new error

            :param errors: string with current errors
            :param new_error: string with new error to be added
        """
        return "{}{}\n".format(
            errors, new_error
        )

    def _lot_vals(self, product, lot_serial_search, date=False):
        """ Returns a list of dicionaries with the lots/serial info

            :param product: product.product record
            :param lot_serial_search: search option (all or available)
            :param date: string with date information
        """
        domain = [('product_id', '=', product.id)]
        lot_vals = []
        lot_ids = self.env['stock.production.lot'].search(domain)
        # Se realiza primero una búsqueda general y luego un filtro
        # porque el campo product_qty no está almacenado
        if lot_serial_search == 'available':
            lot_ids = lot_ids.filtered(
                lambda a: a.product_qty > 0.0
            )
        if lot_serial_search == 'all' and date:
            lot_ids = lot_ids.filtered(
                lambda a: a.product_qty > 0.0 or a.create_date >= datetime.strptime(date, "%Y-%m-%d")
            )            
        for lot in lot_ids:
            lot_vals.append(
                {
                    'name': lot.name,
                    'internalRef': lot.ref,
                    'quantity': lot.product_qty
                }
            )
        return lot_vals

    def _product_vals(self, product, ecommerce_connection, lot_serial_search=False, lot_serial_date=False):
        """ Returns dictionary with the producto info

            :param product: product.product record
            :param ecommerce_connection: ecommerce.connection record
            :param lot_serial_search: search option (all or available)
            :param lot_serial_date: string with date information
        """
        ecommerce_id = False
        ecommerce_product = product.ecommerce_product_ids.filtered(
            lambda a: a.ecommerce_id == ecommerce_connection
        )
        if ecommerce_product:
            ecommerce_id = ecommerce_product.ecommerce_id
        vals = {
            'product': product.display_name,
            'odooId': product.id,
            'ecommerceId': ecommerce_id,
            'sku': product.default_code,
            'barcode': product.barcode,
            'available': product.qty_available,
            'virtual': product.virtual_available,
            'tracking': product.tracking,
        }

        if lot_serial_search and product.tracking in ['serial', 'lot']:
            vals['lot_serial'] = self._lot_vals(product, lot_serial_search, lot_serial_date)

        return vals

    def _check_values(self, values, errors):
        """ Returns string with found errors

            :param values: dictionary with the call values
            :param errors: string with errors
        """

        # Check company
        if not values.get('companyId'):
            errors = self._write_errors(errors, "Company ID must be provided.")
        else:
            company = int(values.get('companyId'))
            company_id = self.env['res.company'].search([
                ('id', '=', company)
            ], limit=1)            
            if not company_id:
                errors = self._write_errors(errors, "Company not found.")
            elif not company_id.accept_stock_check_connector:
                errors = self._write_errors(errors, "The company does not accept the external call.")

            # Check Ecommerce Connection
            else:
                if not values.get('ecommerceId'):
                    errors = self._write_errors(errors, "Ecommerce ID must be provided.")
                else:
                    ecommerce_connection = self.env['ecommerce.connection'].search([
                        ('ecommerce_id', '=', int(values.get('ecommerceId'))),
                        ('company_id', '=', company_id.id)
                    ], limit=1)
                    if not ecommerce_connection:
                        errors = self._write_errors(errors, "Ecommerce connection not found.")

        # Check products
        if values.get('products'):
            for p in values.get('products'):
                if any(not p.get('searchKey') for p in values.get('products')):
                    errors = self._write_errors(errors, "Search Key must be present in all products.")
                elif any(p.get('searchKey') not in SEARCH_KEYS for p in values.get('products')):
                    errors = self._write_errors(errors, "Search Key value is not correct in some products.")
                elif any(not p.get('searchVal') for p in values.get('products')):
                    errors = self._write_errors(errors, "Search Value must be present in all products.")
                if errors:
                    break

        # Check lot/serial values
        if values.get('lotSerialSearch') and values.get('lotSerialSearch') not in ['available', 'all']:
            errors = self._write_errors(errors, "Wrong lot/serial search value.")

        return errors

    def _find_product(self, search_key, search_val, ecommerce_connection):
        """ Returns a product.product record

            :param search_key: string with the type of search
            :param search_val: string with the value to be found
            :param search_val: int with the company id
        """
        product_id = False

        if search_key == 'ecommerceId':
            ecommerce_product_id = self.env['ecommerce.product.product'].search([
                ('ecommerce_connection_id', '=', ecommerce_connection.id),
                ('ecommerce_id', '=', int(search_val))
            ], limit=1)
            if ecommerce_product_id:
                product_id = ecommerce_product_id.product_id
        else:
            domain = [
                ('company_id', 'in', [False, ecommerce_connection.company_id.id])
            ]
            if search_key == 'odooId':
                domain += [('id', '=', int(search_val))]
            elif search_key == 'sku':
                domain += [('default_code', '=', search_val)]
            elif search_key == 'barcode':
                domain += [('barcode', '=', search_val)]
            product_id = self.env['product.product'].search(domain, limit=1)

        return product_id

    def _external_stock_check(self, values, errors, products, ecommerce_connection):
        if errors:
            vals = {
                'status': 'error',
                'error_message': errors
            }
        else:
            result_list = []
            for product in products:
                result_list.append(
                    self._product_vals(
                        product,
                        ecommerce_connection,
                        values.get('lotSerialSearch'),
                        values.get('lotSerialDate')
                    )
                )
            vals = {
                'status': 'OK',
                'result': result_list
            }
        return json.dumps(vals)

    @api.model
    def external_stock_check(self, values):
        errors = ""
        errors = self._check_values(values, errors)
        products = self.env['product.product']
        ecommerce_connection = False
        if not errors:
            if not values.get('products'):
                products = self.env['product.product'].search([])
            else:
                ecommerce_connection = self.env['ecommerce.connection'].search([
                    ('ecommerce_id', '=', int(values.get('ecommerceId'))),
                    ('company_id', '=', int(values.get('companyId')))
                ], limit=1)
                for p in values.get('products'):
                    product = self._find_product(
                        p.get('searchKey'),
                        p.get('searchVal'),
                        ecommerce_connection,
                    )
                    if not product:
                        errors = self._write_errors(errors, "Product with search key {} and value {} could not be found.". format(
                            p.get('searchKey'),
                            p.get('searchVal')                            
                        ))
                        break
                    else:
                        products += product
        return self._external_stock_check(values, errors, products, ecommerce_connection)
