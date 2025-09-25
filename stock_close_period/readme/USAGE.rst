**Creating a Stock Closing Period**

1. Navigate to *Inventory > Stock Close Period > Stock Close Period*
2. Click **Create** to start a new closing period
3. Configure the following fields:

   * **Reference**: Enter a unique name for this closing (e.g., "2024-Q1 Closing")
   * **Close Date**: Select the date for inventory valuation
   * **Force Evaluation Method**: Choose the costing approach:

     - *Compute based on category setup*: Uses product category configuration
     - *Compute based on purchase average cost*: Calculates from purchase history
     - *Compute based on cost in product*: Uses standard product cost

   * **Last Closed** (optional): Link to previous period for incremental calculations
   * **Bypass Negative Quantity**: Enable to ignore products with negative stock
   * **Force Archive**: Enable to deactivate processed stock moves after closing

**Processing Workflow**

1. **Start - Calculate Quantities**:

   * Click the **Start** button to begin processing
   * System calculates product quantities at the closing date
   * Review and manually adjust quantities if needed (e.g., for consignment stock)
   * The state changes to "In Progress"

2. **Compute Purchase Costs**:

   * Click **Compute Purchase** to calculate product costs
   * System applies the selected evaluation method
   * For purchase average: calculates from purchase orders between periods
   * Process may take time for large inventories

3. **Manual Adjustments** (if needed):

   * Edit individual line items for cost corrections
   * Modify quantities for special cases
   * Add notes or references as needed

4. **Validation**:

   * Review the total stock amount value
   * Click **Validate** to finalize the closing
   * State changes to "Validated"
   * Period becomes read-only

**Using CSV Import**

For bulk inventory data import:

1. Navigate to *Inventory > Stock Close Period > Stock Close Import*
2. Select the target **Stock Close Period**
3. Prepare CSV file with semicolon-separated format:

   .. code-block:: text

      CODE;COST;QTY
      PROD001;15,50;100,00
      PROD002;8,25;250,50
      PROD003;102,00;50,00

   * CODE: Product default code (must exist in system)
   * COST: Unit cost (comma or dot as decimal separator)
   * QTY: Quantity (comma or dot as decimal separator)

4. Upload the file and click **Import**
5. System validates products and creates closing lines
6. The period is automatically marked as "done"
