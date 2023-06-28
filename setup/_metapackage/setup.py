import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-stock-logistics-reporting",
    description="Meta package for oca-stock-logistics-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-delivery_line_sale_line_position>=15.0dev,<15.1dev',
        'odoo-addon-stock_account_quantity_history_location>=15.0dev,<15.1dev',
        'odoo-addon-stock_account_valuation_report>=15.0dev,<15.1dev',
        'odoo-addon-stock_card_report>=15.0dev,<15.1dev',
        'odoo-addon-stock_move_value_report>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_custom_description>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_external_note>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_internal_delivery_address>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_product_sticker>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_undelivered_product>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_valued>=15.0dev,<15.1dev',
        'odoo-addon-stock_picking_report_valued_sale_mrp>=15.0dev,<15.1dev',
        'odoo-addon-stock_quantity_history_location>=15.0dev,<15.1dev',
        'odoo-addon-stock_report_quantity_by_location>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
