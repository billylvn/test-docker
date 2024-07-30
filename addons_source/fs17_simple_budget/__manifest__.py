# -*- coding: utf-8 -*-
{
    'name': "Personal Budget",

    'summary': """
        Budgeting your personal cashflow.""",

    'description': """
        Budgeting your personal cashflow.
    """,

    'author': "Farhan Sabili",
    'website': "https://www.linkedin.com/in/billylvn/",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'mail'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'reports/budget_analysis.xml',
        'views/realization.xml',
        'views/planning.xml',
        'views/category.xml',
        'views/menu_items.xml',
    ],
    'application': True
}
