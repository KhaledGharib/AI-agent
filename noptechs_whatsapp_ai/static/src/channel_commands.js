import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

// Slash commands available in WhatsApp conversations to hand control between the
// AI agent and a human operator: type "/resume" or "/pause" in the composer.
const commandRegistry = registry.category("discuss.channel_commands");

commandRegistry
    .add("resume", {
        channel_types: ["whatsapp"],
        help: _t("Resume automatic AI replies"),
        methodName: "execute_command_resume",
    })
    .add("pause", {
        channel_types: ["whatsapp"],
        help: _t("Pause automatic AI replies (you take over)"),
        methodName: "execute_command_pause",
    });
