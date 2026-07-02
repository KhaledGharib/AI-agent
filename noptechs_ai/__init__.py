from . import controllers
from . import models


def post_init_hook(env):
    """Create the Noptechs AI Agent after the module is first installed."""
    if env['ai.agent'].search([('name', '=', 'Noptechs AI Assistant')], limit=1):
        return  # already exists — don't recreate

    topic = env.ref('noptechs_ai.ai_topic_noptechs', raise_if_not_found=False)

    agent = env['ai.agent'].create({
        'name': 'Noptechs AI Assistant',
        'llm_model': 'gpt-4o',
        'response_style': 'balanced',
        'system_prompt': (
            'You are the Noptechs AI assistant. You help the support team by:\n'
            '- Raising helpdesk tickets from customer issues reported in Discuss channels\n'
            '- Finding or creating customer contacts\n'
            '- Searching the internal Knowledge base for documentation\n'
            '- Creating CRM leads when customers show interest\n\n'
            'Always ask for the Discuss channel ID when raising a ticket so a link back '
            'to the conversation is included. After every action confirm what you did '
            'and share the direct link to the created record.'
        ),
    })

    if topic:
        agent.topic_ids = [(4, topic.id)]
