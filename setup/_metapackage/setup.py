import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-stock-logistics-reporting",
    description="Meta package for oca-stock-logistics-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-stock_account_quantity_history_location',
        'odoo12-addon-stock_account_valuation_report',
        'odoo12-addon-stock_analysis',
        'odoo12-addon-stock_card_report',
        'odoo12-addon-stock_inventory_turnover_report',
        'odoo12-addon-stock_inventory_valuation_report',
        'odoo12-addon-stock_move_value_report',
        'odoo12-addon-stock_picking_comment_template',
        'odoo12-addon-stock_picking_product_label',
        'odoo12-addon-stock_picking_report_custom_description',
        'odoo12-addon-stock_picking_report_undelivered_product',
        'odoo12-addon-stock_picking_report_valued',
        'odoo12-addon-stock_picking_report_valued_sale_mrp',
        'odoo12-addon-stock_quantity_history_location',
        'odoo12-addon-stock_report_quantity_by_location',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
