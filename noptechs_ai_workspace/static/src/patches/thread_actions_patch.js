import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import {
    ThreadAction,
    registerThreadAction,
} from "@mail/core/common/thread_actions";

/**
 * Add an "Expand to Workspace" button to the AI chat-window popup header so the
 * user can jump from the popup into the full-page AI Workspace, on the same
 * conversation.
 */
registerThreadAction("expand-workspace", {
    condition: ({ owner, thread }) =>
        thread?.channel_type === "ai_chat" && owner.props.chatWindow?.isOpen,
    icon: "fa fa-fw fa-window-maximize",
    name: _t("Expand to Workspace"),
    open({ store, thread }) {
        store.env.services.action.doAction({
            type: "ir.actions.client",
            tag: "noptechs_ai_workspace_action",
            params: { channelId: thread.id },
        });
    },
    sequence: 9,
    sequenceGroup: 5,
});

/**
 * The Enterprise `ai` module hides every chat-window action for `ai_chat`
 * channels except a small whitelist. On AI chats we:
 *  - let our own "Expand to Workspace" action through (return `undefined` so the
 *    base `condition` getter uses the action's own `condition`);
 *  - hide "Open in Discuss" (`expand-discuss`), since the Workspace replaces it.
 */
patch(ThreadAction.prototype, {
    _condition({ action, thread }) {
        if (thread?.channel_type === "ai_chat") {
            if (action?.id === "expand-workspace") {
                return undefined;
            }
            if (action?.id === "expand-discuss") {
                return false;
            }
        }
        return super._condition(...arguments);
    },
});
