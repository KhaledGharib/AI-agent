# Part of Noptechs AI Workspace.
from odoo.addons.ai.controllers.main import AIController


class AIWorkspaceController(AIController):

    def _should_unlink_on_close(self, channel):
        """Keep AI chats that contain a real conversation.

        The base `ai` module deletes the channel when its chat-window popup is
        closed, which is why chats never reached the AI Workspace. Here we only
        discard *empty* draft chats (the user opened the popup but never sent a
        message); anything with an actual message is kept so it stays available
        in the workspace and its history.
        """
        has_messages = bool(channel.sudo().message_ids.filtered(
            lambda message: message.message_type == "comment"
        ))
        return super()._should_unlink_on_close(channel) and not has_messages
