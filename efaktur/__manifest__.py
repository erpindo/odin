# -*- coding: utf-8 -*-
{
    'name': "Odin e-Faktur",

    'summary': """
        ERP Indonesia, efaktur module""",

    'description': """
        ERP Indonesia, efaktur module \n
        E-Faktur Menu\n
        Format : 010.000-16.00000001\n
        * 2 (dua) digit pertama adalah Kode Transaksi\n
        * 1 (satu) digit berikutnya adalah Kode Status\n
        * 3 (tiga) digit berikutnya adalah Kode Cabang\n
        * 2 (dua) digit pertama adalah Tahun Penerbitan\n
        * 8 (delapan) digit berikutnya adalah Nomor Urut\n
    """,

    'author': "ERP Indonesia",
    'website': "https://erpindonesia.co.id",

    'category': 'Accounting',
    'version': '13.0.1',

    'depends': [
        'account'
        ],

    'data': [
        'security/ir.model.access.csv',
        'views/efaktur_view.xml',
        'wizard/reexport_taxnumber_view.xml',
        'wizard/reexport_efaktur.xml',
        'wizard/upload_efaktur_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 2,
}
