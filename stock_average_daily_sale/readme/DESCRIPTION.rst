This module allows to gather stock consumptions and build reporting for average
daily consumptions. Technically, this has been done through a materialized
postgresql view in order to be as fast as possible (some other flow modules can
depend on this).

You can add several configurations depending on the location from which
consumptions are counted.

For each product ABC classification, you can define the computation horizon,
i.e. the amount of time to look backward (in days or weeks or months or years).

You can exclude some days of the week like saturday and sunday from the
computation. However, if moves occurs on those excluded days, they are still counted.
If your warehouse is open usualy on week days, the averages will be on 5 days a
week. If the warehouse had some activity during the week-end, this will be
considered in the total and average as if it happened during weekdays.

The report also provides a recommended quantity. That recommended quantity is the biggest between:
- a coverage in days * the average daily consumption + a safety
- a coverage in days * the average consumption

The second part tries to better recommend a quantity for C products.
The safety is computed as:
daily standard deviation * sqrt(coverage) * a safety factor
It is up to you to configure the safety factor.
