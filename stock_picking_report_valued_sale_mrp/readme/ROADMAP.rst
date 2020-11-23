* Matching selled kits and their delivered components it's quite tricky. There
  are two possible approaches to findout from the component how many units
  correspond with every whole kit:

  - We could have a link to the original BoM line and guess it from it. This
    approach is the one that Odoo has taken in v13 with the sale order line
    deliveried quantities computation. The main issue is that if the original
    BoM changes then we'd loose the correct units per kit reference.

  - Another aproach (the one in this module) is to compute the component units
    per kit matching the sale order line and its related moves demands. But if
    the user manually adjust the demand on one model without adjusting it in
    the order we'll have an incorrect reference as well.
