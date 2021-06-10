import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-stock-logistics-reporting",
    description="Meta package for oca-stock-logistics-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-stock_account_quantity_history_location',
        'odoo13-addon-stock_card_report',
        'odoo13-addon-stock_inventory_valuation_show_remaining',
        'odoo13-addon-stock_picking_report_undelivered_product',
        'odoo13-addon-stock_picking_report_valued',
        'odoo13-addon-stock_picking_report_valued_sale_mrp',
        'odoo13-addon-stock_quantity_history_location',
        'odoo13-addon-stock_report_quantity_by_location',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
