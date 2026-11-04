* Matching selled kits and their delivered components it's quite tricky. There
  are two possible approaches to findout from the component how many units
  correspond with every whole kit:

  - We could have a link to the original BoM line and guess it from it. This
    approach is the one that Odoo has taken in v13 with the sale order line
    deliveried quantities computation, and the one this module uses when the
    component move has it. The kits are deduced from a component the BoM
    tells: when the BoM rounds a component and the sale line was exploded
    more than once (quantity raised after confirming), its moves don't match
    the BoM and another component is used. The main issue is that if the
    quantities of the original BoM change then we'd loose the correct units
    per kit reference.

  - Another aproach (the fallback in this module, when the moves don't tell
    the BoM line) is to compute the component units per kit matching the sale
    order line and its related moves demands. But if the user manually adjust
    the demand on one model without adjusting it in the order we'll have an
    incorrect reference as well.
