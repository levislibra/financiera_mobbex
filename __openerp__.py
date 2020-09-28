# -*- coding: utf-8 -*-
{
    'name': "Financiera Mobbex",

    'summary': """
        Suscripcion para el cobro de cuotas por debito automatico en la
				tarjeta de debito.""",

    'description': """
        Suscripcion para el cobro de cuotas por debito automatico en la
				tarjeta de debito.
    """,

    'author': "Librasoft",
    'website': "https://libra-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'financiera_prestamos'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mobbex_config.xml',
				'views/extends_res_company.xml',
				'views/extends_financiera_prestamo.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}