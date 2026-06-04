# -*- coding: utf-8 -*-
{
    'name': "Top Customers Invoice & Vendor Bill Analytics",
    'version': '14.0.1.0.0',
    'category': 'accounting',
    'sequence': 10,
    'summary': " Top Customer and Vendor analytics with comparison and PDF/Excel export support. ",
    'license': 'OPL-1',
    'description': """ This module helps analyze Top Customer Invoices and Vendor Bills in Odoo based on total amount, total orders, and quantity. It provides smart filtering, previous period comparison, and detailed analytics reports to improve sales and purchase analysis. The module supports invoice status filtering and allows exporting reports in PDF and Excel formats for better business reporting.
    """,
    'author': "Prefortune Technologies LLP",
    'website': "https://www.prefortune.com/",
    'maintainer': 'Prefortune Technologies LLP',
    "support": "odoo@prefortune.com",
    'currency': 'EUR',
	'price': '0.00',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'report/account_top_customer_vendor_report.xml',
        'wizard/account_top_customer_vendor_wizard_view.xml',
        'views/account_menu_views.xml',
    ],
    "images": ["static/description/banner.png"],
    'installable' : True,
    'application': True,
    'auto_install' : False,

}
