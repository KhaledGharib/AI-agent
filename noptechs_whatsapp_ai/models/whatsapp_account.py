# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    ai_agent_id = fields.Many2one(
        comodel_name='ai.agent',
        string="AI Agent",
        domain=[('is_system_agent', '=', False)],
        help="If set, this AI agent automatically answers inbound WhatsApp "
             "conversations for this account until a human operator takes over.",
    )
    ai_auto_reply = fields.Boolean(
        string="AI Auto-Reply",
        default=True,
        help="When enabled, the AI agent replies to inbound messages without "
             "waiting for a human operator. Disable to keep the agent available "
             "but silent.",
    )
