{
    'name': "Noptechs AI",
    'summary': "AI assistant endpoints: tickets, contacts, knowledge, and CRM",
    'description': """
        Registers four AI tools inside Odoo's built-in ai.agent system so the
        AI assistant can — using the API key already configured in Odoo Settings:
        - Raise helpdesk tickets from customer-facing Discuss channels
        - Search and create contacts (res.partner)
        - Search Knowledge articles (restricted by folders you pick in Settings)
        - Create CRM leads
    """,
    'author': "Noptechs",
    'website': "https://www.noptechs.com",
    'category': 'Technical',
    'version': '19.0.1.0.0',

    # 'ai' and 'helpdesk' are Enterprise-only modules.
    # Remove them if you are on Community edition (and remove the matching tools).
    'depends': ['base', 'mail', 'helpdesk', 'knowledge', 'crm', 'ai', 'ai_app'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/views.xml',
        'data/ai_tools.xml',
    ],

    'post_init_hook': 'post_init_hook',

    'installable': True,
    'application': False,
    'auto_install': False,
}
