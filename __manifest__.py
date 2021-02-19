# -*- coding: utf-8 -*-
{
    'name': "Upwork invoice",

    'summary': """upwork invoice""",

    'description': """
        This Module:
            - Import invoices from Upwork
            - Create records based on imports
    """,

    'author': "Mounir lahsini",
    'website': "https://github.com/matteopolleschi/upwork_invoice_import",

    'category': 'Accounting',
    'version': '1.0',

    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_it_fiscalcode',
        'l10n_it_fatturapa_out',

    ],

    'data': [
        'security/ir.model.access.csv',
        'views/upwork_invoice_views.xml',
        'views/upwork_invoice_rate_views.xml',
    ],

    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
