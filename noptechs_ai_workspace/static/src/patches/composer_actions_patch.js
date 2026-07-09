import { patch } from "@web/core/utils/patch";
import { ComposerAction } from "@mail/core/common/composer_actions";

// Composer actions the base agent couldn't make use of before, but ours now
// can: file/image/document uploads and voice messages (see ai_agent.py
// `_get_message_files`, which reads and transcribes them).
const ENABLED_ACTIONS_FOR_AI_CHAT = ["upload-files", "voice-start", "voice-stop", "voice-recording"];

/**
 * The Enterprise `ai` module hides every composer action except "send-message"
 * for AI chats (any thread whose correspondent is an agent), since the base
 * agent doesn't read attachments. Let the actions above through as well.
 */
patch(ComposerAction.prototype, {
    _condition({ composer }) {
        if (
            composer.targetThread?.correspondent?.persona.im_status === "agent" &&
            ENABLED_ACTIONS_FOR_AI_CHAT.includes(this.id)
        ) {
            // Returning undefined (instead of delegating to the `ai` module's
            // patch, which hard-blocks it) lets the action fall back to its
            // own registered condition.
            return undefined;
        }
        return super._condition(...arguments);
    },
});
