1. **Enable the connector on the company**: Go to Settings > Companies > [your company], open the Ecommerce Connector tab
and activate the checkbox Accept Ecommerce Connector.

2. **Create a Connection**: Go to Ecommerce Connector > Connection and create a new record:
    - Name: a descriptive label (e.g. "Shop")
    - Ecommerce ID: a unique numeric identifier agreed with the e-commerce platform
    - Company: the Odoo company that will own the imported orders
    - Language: language used for multilanguage fields

3. **Configure order and invoice behaviour**:
    - Enable Create Invoice if invoices should be generated automatically
    - Enable Validate Invoice to confirm them automatically
    - Enable Use Odoo Sales Seq. to use Odoo numbering instead of the ecommerce reference
    - Enable Check Customer VAT for VAT validation on business customers
4. **Configure search rules**: Define how records are matched:
    - Products: Ecommerce ID, SKU or Barcode
    - Contacts: Ecommerce ID, Email, VAT or Contact Info
    - Addresses: Ecommerce ID, Email or Contact Info

For more information, check the operations manual provided by Sygel.
