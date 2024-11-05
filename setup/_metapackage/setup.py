import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-sygel-technology-sy-general-connector",
    description="Meta package for sygel-technology-sy-general-connector Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ecommerce_connector',
        'odoo14-addon-ecommerce_connector_sii',
        'odoo14-addon-product_management_connector',
        'odoo14-addon-stock_check_connector',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
