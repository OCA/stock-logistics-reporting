**User Access Configuration**

1. **Security Groups**:

   * **Stock Close Period Manager** (``stock_close_period.group_stock_close_period_manager``):

     - Full access to create, edit, validate, and delete closing periods
     - Access to import wizard and all reporting functions
     - Can archive stock moves and force evaluation methods

   * **Stock Close Period User Read Only** (``stock_close_period.group_stock_close_period_user_readonly``):

     - View-only access to closing periods and reports
     - Cannot modify or create new periods

2. **User Assignment**:

   Go to *Settings > Users & Companies > Users*:

   - Select the user to configure
   - Assign appropriate Stock Close Period group

**System Parameters**

The module uses a system parameter for default configuration:

* **Default Last Close Date**: ``stock_close_period.default_last_close_date``

  - Default value: 2010-01-01
  - Can be modified via *Settings > Technical > System Parameters*
  - Used when no previous closing period is selected

**Performance Settings**

Consider these optional configurations for large databases:

* **Archive Stock Moves**: Enable the "Force Archive" option in closing periods to deactivate processed moves
* **Bypass Negative Quantities**: Enable to skip products with negative stock during calculations
