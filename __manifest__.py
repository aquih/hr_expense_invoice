# -*- coding: utf-8 -*-

{
    'name': 'Gastos unidos a facturas',
    'version': '2.3',
    'category': 'Accounting/Expenses',
    'sequence': 6,
    'summary': 'Gastos unidos a facturas',
    'description': """ Cambios a gastos para unirlas a facturas """,
    'website': 'http://www.aquih.com',
    'author': 'Rodrigo Fernandez',
    'depends': ['hr_expense'],
    'data': [
        'wizard/hr_expense_invoice_crear_gasto_views.xml',
        'views/hr_expense_views.xml',
        'security/hr_expense_invoice_security.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other OSI approved licence',
}
