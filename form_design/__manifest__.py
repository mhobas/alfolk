# -*- coding: utf-8 -*-
{
    'name': "Form Design",

    'summary': """
      free create and fill forms""",

    'description': """
    """,

    'author': "Alzahraa Gamal",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['hr', 'mail', 'web_widget_x2many_2d_matrix','partner_category'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/applyLine.xml',
        'views/apply.xml',
        'views/partner.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
