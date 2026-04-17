================
POSTMAN EXAMPLES
================


This folder contains the ecommerce_connector_sii_collection_v18.postman_collection.json.

A template with examples of standard calls from Sygel's ecommerce_connector_sii module in v18

To use it:

- Import the template into your personal workspace
- Review the general variables, and configure them with those of the odoo to connect
- Going up the current value of the sale_id variable as you create orders

It has the following calls:

-  **External Create Sale for SII**: Call to create a sale, but using an individual customer without a tax ID number. Required to test the ecommerce_connector_sii module.
