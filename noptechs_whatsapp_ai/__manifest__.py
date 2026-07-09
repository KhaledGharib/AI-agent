# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "WhatsApp AI Agent",
    'summary': "Let an AI agent answer WhatsApp conversations automatically",
    'description': """
WhatsApp AI Agent
=================

Bridges the AI module (``ai`` / ``ai_livechat``) with the WhatsApp module so an
``ai.agent`` can handle inbound WhatsApp conversations and reply to customers
directly on WhatsApp.

How it works
------------
* You assign an AI agent to a WhatsApp Business Account.
* When a customer sends a WhatsApp message, Odoo creates/updates the WhatsApp
  ``discuss.channel`` as usual, then triggers the configured agent server-side.
* The agent's reply is posted into the channel as a ``whatsapp_message``, which
  the standard WhatsApp pipeline relays back to the customer.
* As soon as a human operator replies in the channel, the AI is paused for that
  conversation (handover). It can be resumed from the channel.
""",
    'category': 'WhatsApp',
    'version': '19.0.1.0.0',
    'depends': ['whatsapp', 'ai'],
    'data': [
        'data/ir_cron.xml',
        'views/whatsapp_account_views.xml',
        'views/discuss_channel_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'noptechs_whatsapp_ai/static/src/**/*',
        ],
    },
    'author': 'Noptechs',
    'license': 'OPL-1',
}
