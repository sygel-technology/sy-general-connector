================
POSTMAN EXAMPLES
================


This folder contains the ecommerce_connector_collection_v18.postman_collection.json. 

A template with examples of standard calls from Sygel's ecommerce_connector module in v18

To use it:

- Import the template into your personal workspace
- Review the general variables, and configure them with those of the odoo to connect
- Going up the current value of the sale_id variable as you create orders

It has the following calls:

-  **External Create Sale**: Call to create a sale, and the rest of the necessary associated records: customer, products, etc. Several examples are offered to test the call with different clients, products, prices, discounts, countries, currencies...
-  **External Update Partner**: Call to update the data of a previously created customer
-  **External Create Credit Note**: Call to create a corrective invoice. Examples are provided for creating a full and a partial invoice. Partial example 1 corrects the invoice created in the sales order of example 1, and the same applies to example 2.
