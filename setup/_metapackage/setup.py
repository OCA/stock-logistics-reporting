import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-stock-logistics-reporting",
    description="Meta package for oca-stock-logistics-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-stock_picking_comment_template',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
