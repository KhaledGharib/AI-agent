# Part of Noptechs AI Workspace.
import base64
import logging

from odoo import models

from odoo.addons.ai.utils.llm_api_service import LLMApiService

_logger = logging.getLogger(__name__)

# Keep in line with noptechs_whatsapp_ai's own cap so LLM request size/cost
# stays reasonable regardless of which channel triggered the agent.
MAX_ATTACHMENTS_PER_MESSAGE = 5
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20 MB


class AiAgent(models.Model):
    _inherit = 'ai.agent'

    def _get_message_files(self, mail_message, channel):
        if channel.channel_type != 'ai_chat' or not mail_message.attachment_ids:
            return super()._get_message_files(mail_message, channel)

        provider = self._get_provider()
        attachments = mail_message.attachment_ids
        files = []
        unread = []

        for attachment in attachments[:MAX_ATTACHMENTS_PER_MESSAGE]:
            mimetype = attachment.mimetype or ''
            if attachment.file_size > MAX_ATTACHMENT_SIZE:
                unread.append(attachment.name or mimetype or "file")
                continue

            if mimetype.startswith('image/') or mimetype == 'application/pdf':
                files.append({'mimetype': mimetype, 'value': base64.b64encode(attachment.raw).decode()})
            elif mimetype == 'text/plain':
                files.append({'mimetype': mimetype, 'value': attachment.raw.decode('utf-8', errors='ignore')})
            elif mimetype.startswith('video/') and provider == 'google':
                # Only Gemini can natively read video content; other providers can't.
                files.append({'mimetype': mimetype, 'value': base64.b64encode(attachment.raw).decode()})
            elif mimetype.startswith('audio/') and (transcript := self._ai_workspace_transcribe(attachment)):
                files.append({'mimetype': 'text/plain', 'value': f"[Voice message transcript]: {transcript}"})
            else:
                unread.append(attachment.name or mimetype or "file")

        if len(attachments) > MAX_ATTACHMENTS_PER_MESSAGE:
            unread.append(f"and {len(attachments) - MAX_ATTACHMENTS_PER_MESSAGE} more attachment(s)")

        if unread:
            files.append({
                'mimetype': 'text/plain',
                'value': (
                    "[The user also sent the following attachment(s) which you cannot read with your "
                    f"current capabilities: {', '.join(unread)}. Acknowledge them politely and, if needed "
                    "to answer, ask the user to describe the content or resend it as an image or PDF.]"
                ),
            })

        return files

    def _ai_workspace_transcribe(self, attachment):
        """Transcribe a voice/audio attachment with Whisper so the agent can react to it."""
        try:
            return LLMApiService(env=self.env, provider='openai').get_transcription(
                attachment.raw, mimetype=attachment.mimetype or 'audio/ogg',
            )
        except Exception:
            _logger.exception("AI Workspace: failed to transcribe audio attachment %s", attachment.name)
            return None
