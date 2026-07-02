{
    'name': "Noptechs AI Workspace",
    'summary': "Full-page AI chat workspace with persistent conversation history",
    'description': """
        Adds a full-page AI chat workspace (Open WebUI style) alongside Odoo's
        built-in AI assistant:

        - A "Workspace" menu under the standard "AI" app, with a sidebar of past
          conversations and a large chat panel.
        - AI conversations are kept (the built-in 1-day auto-purge is disabled);
          only abandoned, empty draft chats are cleaned up.
        - The AI chat-window popup gets an "Expand to Workspace" button to jump
          into the full-page view on the same conversation.

        This module only adds to / overrides via the registry. It does not edit
        the Enterprise `ai` module.
    """,
    'author': "Noptechs",
    'website': "https://www.noptechs.com",
    'category': 'Productivity/Discuss',
    'version': '19.0.1.0.0',

    # `ai` provides the agents/chat backend; `ai_app` provides the "AI" root
    # menu the Workspace is hung under.
    'depends': ['ai', 'ai_app', 'mail'],

    'data': [
        'views/ai_workspace_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'noptechs_ai_workspace/static/src/**/*',
            # Dark-mode overrides belong to the dark bundle only.
            ('remove', 'noptechs_ai_workspace/static/src/**/*.dark.scss'),
        ],
        'web.assets_web_dark': [
            'noptechs_ai_workspace/static/src/**/*.dark.scss',
        ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
