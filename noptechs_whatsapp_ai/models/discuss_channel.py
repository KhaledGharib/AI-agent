# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, fields, models
from odoo.addons.mail.tools.discuss import Store
from odoo.addons.whatsapp.models.discuss_channel import is_whatsapp_channel

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    # When True, the AI agent stops auto-replying on this conversation because a
    # human operator has taken over. Can be resumed manually.
    whatsapp_ai_paused = fields.Boolean(string="WhatsApp AI Paused", copy=False)
    # The last inbound customer message awaiting an AI answer. Picked up by the
    # cron so the webhook request can return immediately.
    whatsapp_ai_pending_message_id = fields.Many2one(
        comodel_name='mail.message', string="WhatsApp AI Pending Message",
        index='btree_not_null', copy=False,
    )
    # Whether this channel's account has an AI agent (drives the chat-window
    # Resume/Pause AI buttons). Not stored — only exposed to the web client.
    whatsapp_has_ai_agent = fields.Boolean(compute="_compute_whatsapp_has_ai_agent")

    @api.depends("wa_account_id.ai_agent_id")
    def _compute_whatsapp_has_ai_agent(self):
        for channel in self:
            channel.whatsapp_has_ai_agent = bool(channel.wa_account_id.ai_agent_id)

    def _to_store_defaults(self, target):
        # Expose the handover state to the web client so the conversation can
        # show a Resume/Pause AI button.
        return super()._to_store_defaults(target) + [
            Store.Attr("whatsapp_ai_paused", predicate=is_whatsapp_channel),
            Store.Attr("whatsapp_has_ai_agent", predicate=is_whatsapp_channel, sudo=True),
        ]

    def _whatsapp_ai_sync_paused(self):
        """Push the current pause state to everyone viewing the conversation."""
        for channel in self:
            Store(bus_channel=channel).add(channel, "whatsapp_ai_paused").bus_send()

    def message_post(self, *args, body='', attachment_ids=None, message_type='notification', parent_id=False, **kwargs):
        message = super().message_post(
            *args, body=body, attachment_ids=attachment_ids,
            message_type=message_type, parent_id=parent_id, **kwargs
        )
        if (
            message
            and message_type == 'whatsapp_message'
            and self.channel_type == 'whatsapp'
            and self.wa_account_id.ai_agent_id
        ):
            self._whatsapp_ai_after_post(message, kwargs)
        return message

    def _whatsapp_ai_after_post(self, message, post_kwargs):
        """React to a freshly posted WhatsApp message.

        * Inbound customer message -> queue an AI reply (unless paused/disabled).
        * Outbound message from a human operator -> pause the AI (handover).
        """
        self.ensure_one()
        account = self.wa_account_id
        agent = account.ai_agent_id
        inbound = bool(post_kwargs.get('whatsapp_inbound_msg_uid'))

        if inbound:
            if (
                account.ai_auto_reply
                and not self.whatsapp_ai_paused
                and message.body
                and message.body.strip()
            ):
                self.sudo().whatsapp_ai_pending_message_id = message.id
                self.env.ref('noptechs_whatsapp_ai.ir_cron_whatsapp_ai_reply').sudo()._trigger()
            return

        # Outbound message: detect a human operator stepping in.
        author_id = post_kwargs.get('author_id') or message.author_id.id
        if (
            author_id
            and author_id not in (agent.partner_id.id, self.whatsapp_partner_id.id)
            and not self.whatsapp_ai_paused
        ):
            self.sudo().whatsapp_ai_paused = True
            self._whatsapp_ai_sync_paused()
            self.message_post(
                body=_("Automatic AI replies have been paused for this conversation "
                       "because an operator replied."),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                author_id=self.env.ref('base.partner_root').id,
            )

    @api.model
    def _cron_whatsapp_ai_reply(self):
        """Generate AI answers for conversations with a pending customer message."""
        channels = self.sudo().search([('whatsapp_ai_pending_message_id', '!=', False)])
        for channel in channels:
            message = channel.whatsapp_ai_pending_message_id
            # Clear the pending flag first so a failure doesn't loop forever.
            channel.whatsapp_ai_pending_message_id = False
            agent = channel.wa_account_id.ai_agent_id
            if (
                not agent
                or channel.whatsapp_ai_paused
                or not channel.wa_account_id.ai_auto_reply
            ):
                continue
            try:
                agent._generate_response_for_channel(message, channel)
                self.env.cr.commit()
            except Exception:  # noqa: BLE001 - never let one channel break the batch
                self.env.cr.rollback()
                _logger.exception(
                    "WhatsApp AI agent %s failed to answer channel %s", agent.id, channel.id
                )

    def action_whatsapp_ai_resume(self):
        """Re-enable automatic AI replies on this conversation."""
        self.whatsapp_ai_paused = False
        self._whatsapp_ai_sync_paused()
        return True

    def action_whatsapp_ai_pause(self):
        """Stop automatic AI replies on this conversation."""
        self.whatsapp_ai_paused = True
        self._whatsapp_ai_sync_paused()
        return True

    # ------------------------------------------------------------------
    # Slash commands (/resume, /pause) usable from the WhatsApp composer
    # ------------------------------------------------------------------
    def execute_command_resume(self, **kwargs):
        self._whatsapp_ai_command_set_paused(False)

    def execute_command_pause(self, **kwargs):
        self._whatsapp_ai_command_set_paused(True)

    def _whatsapp_ai_command_set_paused(self, paused):
        self.ensure_one()
        if self.channel_type != 'whatsapp' or not self.wa_account_id.ai_agent_id:
            self.env.user._bus_send_transient_message(
                self, _("No AI agent is configured for this conversation.")
            )
            return
        self.whatsapp_ai_paused = paused
        self._whatsapp_ai_sync_paused()
        msg = (
            _("AI paused — you are now handling this conversation.")
            if paused
            else _("AI resumed — the assistant will answer new messages.")
        )
        self.env.user._bus_send_transient_message(self, msg)
