# -*- coding: utf-8 -*-
# Copyright 2022 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Website Google Feed',
    'category': 'Website',
    'version': '16.0.1.0.0',
    'summary': 'Generates a XML feed to be fetch by GMC',
    'author': "ERPGap",
    'website': "https://www.erpgap.com/",
    'maintainer': 'ERPGap',
    'license': 'LGPL-3',
    'depends': [
        'website_sale', 'stock', 'sale_management'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/website_feed.xml',
        'views/google_merchant_script.xml',
        'views/brand_views.xml',
        'views/res_config_settings.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
