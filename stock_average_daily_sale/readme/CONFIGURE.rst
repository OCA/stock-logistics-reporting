* To configure data analysis, you should go to Inventory > Configuration > Average daily sales computation parameters

* You need to fill in the following informations:

  * The product ABC classification you want - see product_abc_classification module
  * The concerned warehouse
  * The stock location for which you want to compute the usage
  * The period of time to analyze back (in days/weeks/months/years)
  * A safety factor

* Go to Configuration > Technical > Scheduled Actions > Refresh average daily sales materialized view

  By default, the scheduled action is set to refresh data each day. Note that
  the current day is not take into consideration in the computations, so you
  better run the scheduled action on the early morning.

  WARNING: The current query is not TZ compliant. So the cron must run after midnight UTC time.

* By default, the root location where analysis is done is the Warehouse stock location,
  but you can change it and you can compute usage for multiple locations of the warehouse.
  Ensure to set a location that is used by the stock moves or a parent one.
