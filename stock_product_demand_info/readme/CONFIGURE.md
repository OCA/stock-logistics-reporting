Go to *General Settings* > *Inventory* > *Products* > *Demand periods*.

Enable or create the periods you want to see in the indicators.

![settings](static/description/settings.png)

The periods are defined using the same relative date expression syntax used in
`Domains` in Odoo.

![periods](static/description/periods.png)

For example:

- `today -7d` for the last 7 days
- `today =1d -1m` for the last month
- `today =1d -1y` for the last year
