# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.tools import plaintext2html


class AiAgent(models.Model):
    _inherit = 'ai.agent'

    def _post_ai_response(self, channel, message):
        # On WhatsApp channels the reply must be posted as a 'whatsapp_message'
        # so the standard WhatsApp pipeline relays it back to the customer.
        # (The base implementation posts a plain 'comment', which stays internal.)
        if channel.channel_type == 'whatsapp':
            channel.sudo().message_post(
                author_id=self.partner_id.id,
                body=plaintext2html(message),
                message_type='whatsapp_message',
                subtype_xmlid='mail.mt_comment',
            )
            return
        return super()._post_ai_response(channel, message)
