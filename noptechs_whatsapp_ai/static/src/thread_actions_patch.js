import { _t } from "@web/core/l10n/translation";
import { registerThreadAction } from "@mail/core/common/thread_actions";

/**
 * Chat-window / Discuss header buttons to hand a WhatsApp conversation back and
 * forth between the AI agent and a human operator.
 *
 * When an operator replies, the server auto-pauses the AI (handover) and pushes
 * the new state over the bus, so "Resume AI" appears without a refresh.
 */
function isWhatsappAiThread(thread) {
    return thread?.channel_type === "whatsapp" && thread.whatsapp_has_ai_agent;
}

registerThreadAction("whatsapp-resume-ai", {
    condition: ({ thread }) => isWhatsappAiThread(thread) && thread.whatsapp_ai_paused,
    icon: "fa fa-fw fa-play",
    name: _t("Resume AI"),
    open: ({ store, thread }) =>
        store.env.services.orm.call("discuss.channel", "action_whatsapp_ai_resume", [[thread.id]]),
    sequence: 11,
    sequenceGroup: 5,
});

registerThreadAction("whatsapp-pause-ai", {
    condition: ({ thread }) => isWhatsappAiThread(thread) && !thread.whatsapp_ai_paused,
    icon: "fa fa-fw fa-pause",
    name: _t("Pause AI"),
    open: ({ store, thread }) =>
        store.env.services.orm.call("discuss.channel", "action_whatsapp_ai_pause", [[thread.id]]),
    sequence: 11,
    sequenceGroup: 5,
});
