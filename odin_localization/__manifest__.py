# -*- coding: utf-8 -*-
{
    'name': "Odin Localization",

    'summary': """
        ERP Indonesia, localization module""",

    'description': """
        ERP Indonesia, localization module
    """,

    'author': "ERP Indonesia",
    'website': "https://erpindonesia.co.id",

    'category': 'General',
    'version': '0.1',

    'depends': [
        'base',
        'mail',
        'contacts',
        'base_address_extended'
        ],

    'data': [
        'security/ir.model.access.csv',
        'views/res_subdistrict_view.xml',
        'views/res_village_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
