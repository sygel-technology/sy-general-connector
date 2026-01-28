This module extends the ecommerce_connector module to set values and perform
procedures related to SII when l10n_es_aeat_sii_oca is installed.

The current version of the module supports the following operation:

* Automatically mark invoices as Simplified for B2C customers (typeClient = individual)
  without VAT when a new contact is created through the connector.

### Notes

The ecommerce_connector module enforces VAT as a mandatory field for business
customers (typeClient = business) in its customer validation logic. As a result,
this module only applies the simplified invoice configuration to B2C customers
(typeClient = individual) without VAT.

This behaviour is inherited from ecommerce_connector and is not overridden by
this module.
