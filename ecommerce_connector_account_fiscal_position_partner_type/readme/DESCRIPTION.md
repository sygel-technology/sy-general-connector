This module extends the functionality of ecommerce_connector to add the fiscal position partner type logic to the ecommerce calls.

Specifically, it adds:
- Automatic fillment of the fiscal_position_type of new ecommerce partners, based in the company_type field.
- Improves the search of fiscal positions to use the fiscal_position_type field as b2c

This module must be installed if the odoo instance has the account_fiscal_position_partner_type and ecommerce_connector modules.
