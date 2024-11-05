import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-sygel-technology-sy-general-connector",
    description="Meta package for sygel-technology-sy-general-connector Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-ecommerce_connector>=15.0dev,<15.1dev',
        'odoo-addon-ecommerce_connector_sale_order_type>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
