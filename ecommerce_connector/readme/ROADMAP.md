Future improvements detected for this module. They should be done in the next migrations to upper versions:

- **Cleanup and encapsulation of duplicated code**. To do if the module is refactored in upper versions.
  - Simplify the error handling pattern. The error list is being continously propagated and checked through all the code. Operations are not aborted if an error is detected.
  - Reduce code of main file. Move functions to other files (not necessary orm models)
  - Simplify _get_contact_domain() function
  - Simplify _get_shipping_contact() function
  - Simplify _get_invoice_contact() function
  - Move every values dict creation to a function for that. Review functions: _create_new_product(), _create_new_product_template(), _create_payments()
  - Move every complex domain creation to a function for that. Review functions: _find_product()
  - Refactor fiscal position and taxes calculation. Documentate its behaviour 
  - Refactor and simplify mandatory_fields checks. Required fields could be defined in a data structure.
  - Refactor and simplify the _create_response() function
  - Refactor and simplify the external_create_sale() function
  - Refactor and simplify the external_create_credit_note() function
  - Review the record matching methods between systems. Linking local and external delivery.carrier and account.payment.mode by name (translated) would probably need a change

- **Improve documentation**

- **Improve postman collection examples**

- Add help tooltips to configuration fields

- **Add unit tests**

- Move account_fiscal_position_partner_type dependency to a glue module
