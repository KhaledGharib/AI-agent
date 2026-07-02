import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

import { Thread } from "@mail/core/common/thread";
import { Composer } from "@mail/core/common/composer";

/**
 * Full-page AI chat workspace (Open WebUI style):
 *  - left sidebar listing the user's persistent AI conversations
 *  - main panel reusing Discuss' Thread + Composer components
 */
export class AIWorkspace extends Component {
    static components = { Thread, Composer };
    static props = ["*"];
    static template = "noptechs_ai_workspace.AIWorkspace";

    setup() {
        this.store = useService("mail.store");
        this.orm = useService("orm");
        this.busService = useService("bus_service");
        this.state = useState({
            chats: [],
            agents: [],
            activeAgentId: null,
            thread: null,
            loading: true,
            jumpPresent: 0,
        });
        this.onMessagePosted = this.onMessagePosted.bind(this);
        // Params passed when the workspace is opened for a specific conversation
        // (e.g. the "Expand to Workspace" button in the AI chat-window popup).
        const params = this.props.action?.params || {};
        this._initialChannelId = params.channelId;
        this._initialPrompt = params.user_prompt;
        onWillStart(async () => {
            await this.loadAgents();
            await this.loadChats();
            this.state.loading = false;
            if (this._initialChannelId) {
                await this.openChat(this._initialChannelId);
                if (this._initialPrompt && this.state.thread) {
                    await this.state.thread.isLoadedDeferred;
                    await this.state.thread.post(this._initialPrompt);
                    this.onMessagePosted();
                }
            }
        });
    }

    async loadAgents() {
        this.state.agents = await this.orm.call("discuss.channel", "ai_workspace_get_agents", []);
        if (this.state.agents.length && !this.state.activeAgentId) {
            this.state.activeAgentId = this.state.agents[0].id;
        }
    }

    async loadChats() {
        this.state.chats = await this.orm.call("discuss.channel", "ai_workspace_list_chats", []);
    }

    onSelectAgent(ev) {
        this.state.activeAgentId = parseInt(ev.target.value, 10);
    }

    async openChat(chatId) {
        const thread = await this.store.Thread.getOrFetch({
            model: "discuss.channel",
            id: Number(chatId),
        });
        if (!thread) {
            return;
        }
        // Make sure we receive the AI's streamed reply over the bus.
        if (thread.busChannel) {
            this.busService.addChannel(thread.busChannel);
        }
        this.state.thread = thread;
    }

    async newChat() {
        if (!this.state.agents.length) {
            return;
        }
        const { channel_id, data } = await this.orm.call(
            "discuss.channel",
            "ai_workspace_new_chat",
            [this.state.activeAgentId]
        );
        this.store.insert(data);
        await this.loadChats();
        await this.openChat(channel_id);
    }

    async deleteChat(chatId, ev) {
        ev.stopPropagation();
        await this.orm.call("discuss.channel", "ai_workspace_delete_chat", [Number(chatId)]);
        if (this.state.thread && this.state.thread.id === chatId) {
            this.state.thread = null;
        }
        await this.loadChats();
    }

    async renameChat(chatId, ev) {
        ev.stopPropagation();
        const current = this.state.chats.find((c) => c.id === chatId);
        const name = window.prompt(_t("Rename conversation"), current ? current.name : "");
        if (name === null) {
            return;
        }
        await this.orm.call("discuss.channel", "ai_workspace_rename_chat", [Number(chatId), name]);
        await this.loadChats();
    }

    isActive(chatId) {
        return this.state.thread && this.state.thread.id === chatId;
    }

    /** Refresh the sidebar after the user sends a message (title + ordering). */
    onMessagePosted() {
        this.state.jumpPresent++;
        this.loadChats();
    }
}

registry.category("actions").add("noptechs_ai_workspace_action", AIWorkspace);
