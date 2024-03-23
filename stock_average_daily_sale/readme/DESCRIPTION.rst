This module allows to gather stock consumptions and build reporting for average daily
sales (aka stock consumptions). Technically, this has been done through a
materialized postgresql view in order to be as fast as possible (some other flow
modules can depend on this).

You can add several configurations depending on the window you want to analyze.
So, you can define criteria to filter data:

* The Warehouse
* The product ABC classification
* The location kind (Zone, Area, Bin)
* The amount of time to look backward (in days or weeks or months or years)

Moreover, you can define:

* A safety factor
* A standard deviation exclusion factor
* A different root location for analysis per Warehouse
