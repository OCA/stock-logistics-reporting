This module extends stock picking reports to display the customer
reference (``partner.ref``).

It enhances both delivery and operational reports to improve
traceability and customer identification in logistics documents.

The reference is resolved using the following priority:

1. Picking partner reference (``partner_id.ref``)
2. Commercial partner reference (``partner_id.commercial_partner_id.ref``)

The implementation keeps the logic simple and aligned with standard
Odoo report behavior, avoiding unnecessary complexity.
