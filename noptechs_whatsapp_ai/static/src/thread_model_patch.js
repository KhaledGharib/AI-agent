import { fields } from "@mail/core/common/record";
import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";

// Handover state synced from the server (see discuss.channel._to_store_defaults),
// used to drive the Resume/Pause AI buttons in WhatsApp conversations.
patch(Thread.prototype, {
    setup() {
        super.setup();
        this.whatsapp_ai_paused = fields.Attr(false);
        this.whatsapp_has_ai_agent = fields.Attr(false);
    },
});
