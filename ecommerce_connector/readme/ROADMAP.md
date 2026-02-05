Future improvements detected for this module. They should be done in the next migrations to upper versions:

- **Create a minimal permission group for the connector bot**
  Currently, orders are created by a user with maximum permissions (settings/admin group).
  The module should provide a dedicated group (e.g. *“General Connector Endpoint Runner”*) that depends only on the required groups to create sales orders. Assigning only this group to a user should guarantee the minimum permissions needed to create orders.

- **Refactor to remove the dependency on `sale_invoice_policy`**
  The module currently relies on `sale_invoice_policy` even though it is not declared in the manifest. If this module is not installed, some order imports fail.
  An additional module should be created to encapsulate and provide the `sale_invoice_policy`-related functionality.

- **Cleanup and encapsulation of duplicated code**

- **Add search views**

- **Add help tooltips to configuration fields**

- **Improve documentation**

- **Add unit tests**
