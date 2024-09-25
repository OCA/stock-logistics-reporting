* To configure data analysis, you should go to Inventory > Configuration > Average daily sales computation parameters

* You need to fill in the following informations:

  * The product ABC classification you want - see product_abc_classification module
  * The concerned Warehouse
  * The stock location kind (Zone, Area, Bin) - see stock_location_zone module
  * The period of time to analyze back (in days/weeks/months/years)
  * A standard deviation exclusion factor
  * A safety factor

* Go to Configuration > Technical > Scheduled Actions > Refresh average daily sales materialized view

  By default, the scheduled action is set to refresh data each 4 hours. You can change
  that depending on your needs.

* By default, the root location where analysis is done is the Warehouse stock location,
  but you can change it.

    * Go to Inventory > Configuration > Warehouses
    * Change the 'Average Daily Sale Root Location' field according your needs
