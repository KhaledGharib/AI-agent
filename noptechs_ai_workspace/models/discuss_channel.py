# Part of Noptechs AI Workspace.
from odoo import _, api, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain
from odoo.tools import html2plaintext

from odoo.addons.mail.tools.discuss import Store

# Sentinel name used for freshly created chats that have not been renamed yet.
NEW_CHAT_NAME = "New chat"


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    @api.autovacuum
    def _remove_ai_chat_channels(self):
        """Override of `ai` to keep AI conversation history.

        The base module deletes every AI chat older than one day, which wipes
        the user's history. Here we only remove *abandoned* draft chats that
        never received a single message; any conversation with real content is
        kept forever and managed by the user from the AI Workspace sidebar.
        """
        self.sudo().search(
            Domain("ai_agent_id", "!=", False)
            & Domain("channel_type", "=", "ai_chat")
            & Domain("last_interest_dt", "<", "-1d")
            & Domain("message_ids", "=", False)
        ).unlink()

    # ------------------------------------------------------------------
    # AI Workspace RPC endpoints (called from the client action)
    # ------------------------------------------------------------------

    @api.model
    def ai_workspace_get_agents(self):
        """Return the AI agents the current user is allowed to chat with."""
        agents = self.env["ai.agent"].sudo().search([])
        agents = agents.filtered(lambda agent: agent._is_user_access_allowed())
        return [{"id": agent.id, "name": agent.name} for agent in agents]

    @api.model
    def ai_workspace_list_chats(self):
        """Return the current user's AI chats, most recent first."""
        channels = self.search(
            Domain("channel_type", "=", "ai_chat") & Domain("is_member", "=", True),
            order="last_interest_dt DESC, id DESC",
        )
        partner = self.env.user.partner_id
        result = []
        for channel in channels:
            agent = channel.sudo().ai_agent_id
            title = channel.name
            # Derive a readable title from the first user message when the chat
            # still carries a default name.
            if not title or title in (agent.name, NEW_CHAT_NAME, _(NEW_CHAT_NAME)):
                first_message = channel.sudo().message_ids.filtered(
                    lambda m: m.message_type == "comment" and m.author_id == partner
                ).sorted("id")[:1]
                preview = html2plaintext(first_message.body or "") if first_message else ""
                title = (preview[:50] + "…") if len(preview) > 50 else preview
                title = title or _("New chat")
            result.append({
                "id": channel.id,
                "name": title,
                "agent_name": agent.name,
                "last_interest_dt": channel.last_interest_dt,
            })
        return result

    @api.model
    def ai_workspace_new_chat(self, agent_id=None):
        """Create a fresh AI chat with the given (or default) agent."""
        Agent = self.env["ai.agent"].sudo()
        agent = Agent.browse(agent_id) if agent_id else self.env["ai.agent"]._get_potential_ask_ai_agent()
        if not agent or not agent.exists():
            agent = Agent.search([], limit=1)
        if not agent:
            raise UserError(_("No AI agent is configured. Please contact your administrator."))
        if not agent._is_user_access_allowed():
            raise AccessError(_("You are not allowed to chat with this AI agent."))
        channel = agent._create_ai_chat_channel(channel_name=_("New chat"))
        return {
            "channel_id": channel.id,
            "data": Store().add(channel).get_result(),
        }

    def _ai_workspace_own_channel(self, channel_id):
        """Return the channel only if it is one of the current user's AI chats."""
        return self.search(
            Domain("id", "=", channel_id)
            & Domain("channel_type", "=", "ai_chat")
            & Domain("is_member", "=", True),
            limit=1,
        )

    @api.model
    def ai_workspace_rename_chat(self, channel_id, name):
        channel = self._ai_workspace_own_channel(channel_id)
        if channel:
            channel.sudo().name = (name or "").strip() or _("New chat")
        return True

    @api.model
    def ai_workspace_delete_chat(self, channel_id):
        channel = self._ai_workspace_own_channel(channel_id)
        if channel:
            channel.sudo().unlink()
        return True
