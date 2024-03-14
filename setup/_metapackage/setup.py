import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-stock-logistics-reporting",
    description="Meta package for oca-stock-logistics-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-delivery_line_sale_line_position>=16.0dev,<16.1dev',
        'odoo-addon-stock_card_report>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_report_custom_description>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_report_internal_delivery_address>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_report_qty_undelivered>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_report_valued>=16.0dev,<16.1dev',
        'odoo-addon-stock_quantity_history_location>=16.0dev,<16.1dev',
        'odoo-addon-stock_report_quantity_by_location>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
