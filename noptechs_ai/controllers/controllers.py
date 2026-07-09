from odoo import http
from odoo.http import request


def _get_descendant_article_ids(env, root_ids):
    """
    Return root_ids plus the IDs of every article nested below them.
    Uses breadth-first search so it works for any depth without recursion limits.
    """
    collected = set(root_ids)
    frontier = list(root_ids)
    while frontier:
        children = env['knowledge.article'].sudo().search(
            [('parent_id', 'in', frontier)]
        )
        new_ids = set(children.ids) - collected
        collected.update(new_ids)
        frontier = list(new_ids)
    return list(collected)


class NoptechsAiController(http.Controller):

    # ------------------------------------------------------------------
    # 1. HELPDESK — raise a ticket from a Discuss channel
    # ------------------------------------------------------------------

    @http.route('/noptechs_ai/create_ticket', type='json', auth='user', methods=['POST'], csrf=False)
    def create_ticket(self, **kw):
        """
        Create a helpdesk ticket from a customer Discuss channel.

        Expected JSON params:
            channel_id  (int)   — ID of the discuss.channel
            subject     (str)   — ticket title
            description (str)   — ticket body / error details
            assignee_id (int)   — optional: res.users ID to assign the ticket to
            team_id     (int)   — optional: helpdesk.team ID
            partner_id  (int)   — optional: res.partner ID for the customer
        """
        channel_id = kw.get('channel_id')
        subject = kw.get('subject') or 'AI Raised Ticket'
        description = kw.get('description', '')
        assignee_id = kw.get('assignee_id')
        team_id = kw.get('team_id')
        partner_id = kw.get('partner_id')

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # Build a direct link back to the source channel
        channel_link = ''
        if channel_id:
            channel_link = f"{base_url}/odoo/discuss/channel-{channel_id}"

        full_description = description
        if channel_link:
            full_description += f"\n\n---\nSource channel: {channel_link}"

        # Validate the channel exists
        if channel_id:
            channel = request.env['discuss.channel'].sudo().browse(int(channel_id))
            if channel.exists():
                full_description += f"\nChannel name: {channel.name}"

        ticket_vals = {
            'name': subject,
            'description': full_description,
        }
        if assignee_id:
            ticket_vals['user_id'] = int(assignee_id)
        if team_id:
            ticket_vals['team_id'] = int(team_id)
        if partner_id:
            ticket_vals['partner_id'] = int(partner_id)

        ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)

        return {
            'success': True,
            'ticket_id': ticket.id,
            'ticket_name': ticket.name,
            'ticket_url': f"{base_url}/odoo/helpdesk/{ticket.id}",
        }

    # ------------------------------------------------------------------
    # 2. CONTACTS — find an existing partner or create a new one
    # ------------------------------------------------------------------

    @http.route('/noptechs_ai/find_or_create_partner', type='json', auth='user', methods=['POST'], csrf=False)
    def find_or_create_partner(self, **kw):
        """
        Search for a contact by email or name.  Creates one if not found
        (unless search_only=True).

        Expected JSON params:
            email       (str)   — searched first (exact, case-insensitive)
            name        (str)   — searched if no email is given; required for creation
            phone       (str)   — optional, stored on creation
            search_only (bool)  — if True, never create; just return matches or empty list
        """
        email = (kw.get('email') or '').strip()
        name = (kw.get('name') or '').strip()
        phone = (kw.get('phone') or '').strip()
        search_only = bool(kw.get('search_only', False))

        # Build search domain — email match takes priority
        if email:
            domain = [('email', '=ilike', email)]
        elif name:
            domain = [('name', 'ilike', name)]
        else:
            return {'error': 'Provide at least an email or a name to search.'}

        partners = request.env['res.partner'].sudo().search(domain, limit=5)

        if partners:
            return {
                'found': True,
                'partners': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'email': p.email or '',
                        'phone': p.phone or '',
                        'is_company': p.is_company,
                    }
                    for p in partners
                ],
            }

        if search_only:
            return {'found': False, 'partners': []}

        # Create a new partner
        if not name:
            return {'error': 'A name is required to create a new contact.'}

        vals = {'name': name}
        if email:
            vals['email'] = email
        if phone:
            vals['phone'] = phone

        partner = request.env['res.partner'].sudo().create(vals)
        return {
            'found': False,
            'created': True,
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email or '',
                'phone': partner.phone or '',
            },
        }

    # ------------------------------------------------------------------
    # 3. KNOWLEDGE — search articles within the allowed folders
    # ------------------------------------------------------------------

    @http.route('/noptechs_ai/search_knowledge', type='json', auth='user', methods=['POST'], csrf=False)
    def search_knowledge(self, **kw):
        """
        Full-text search of Knowledge articles.
        Only articles inside the folders configured in Settings are returned.

        Expected JSON params:
            query  (str) — search term (matches title and body)
            limit  (int) — max results to return (default 10)
        """
        query = (kw.get('query') or '').strip()
        limit = int(kw.get('limit') or 10)

        # Load the allowed root article IDs from Settings
        param = request.env['ir.config_parameter'].sudo().get_param(
            'noptechs_ai.knowledge_article_ids', default=''
        )
        if not param:
            return {
                'articles': [],
                'message': 'No Knowledge folders have been configured in Settings > Noptechs AI.',
            }

        root_ids = [int(x) for x in param.split(',') if x.strip().isdigit()]
        if not root_ids:
            return {'articles': [], 'message': 'No valid Knowledge folder IDs found in settings.'}

        # Expand to all descendants
        allowed_ids = _get_descendant_article_ids(request.env, root_ids)

        domain = [('id', 'in', allowed_ids)]
        if query:
            domain += ['|', ('name', 'ilike', query), ('body', 'ilike', query)]

        articles = request.env['knowledge.article'].sudo().search(domain, limit=limit)

        return {
            'articles': [
                {
                    'id': a.id,
                    'name': a.name,
                    'body': a.body or '',       # HTML — the AI layer should strip tags if needed
                    'parent_id': a.parent_id.id if a.parent_id else None,
                    'parent_name': a.parent_id.name if a.parent_id else None,
                }
                for a in articles
            ],
        }

    # ------------------------------------------------------------------
    # 4. CRM — create a new lead
    # ------------------------------------------------------------------

    @http.route('/noptechs_ai/create_lead', type='json', auth='user', methods=['POST'], csrf=False)
    def create_lead(self, **kw):
        """
        Create a CRM lead (opportunity).

        Expected JSON params:
            name        (str)   — lead title (required)
            partner_id  (int)   — optional: link to an existing res.partner
            email       (str)   — optional: contact email
            phone       (str)   — optional: contact phone
            description (str)   — optional: internal notes / details
            team_id     (int)   — optional: crm.team ID
            user_id     (int)   — optional: res.users ID (salesperson)
        """
        name = (kw.get('name') or '').strip()
        if not name:
            return {'error': 'A lead name is required.'}

        lead_vals = {'name': name}

        partner_id = kw.get('partner_id')
        if partner_id:
            lead_vals['partner_id'] = int(partner_id)

        email = (kw.get('email') or '').strip()
        if email:
            lead_vals['email_from'] = email

        phone = (kw.get('phone') or '').strip()
        if phone:
            lead_vals['phone'] = phone

        description = (kw.get('description') or '').strip()
        if description:
            lead_vals['description'] = description

        team_id = kw.get('team_id')
        if team_id:
            lead_vals['team_id'] = int(team_id)

        user_id = kw.get('user_id')
        if user_id:
            lead_vals['user_id'] = int(user_id)

        lead = request.env['crm.lead'].sudo().create(lead_vals)

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'success': True,
            'lead_id': lead.id,
            'lead_name': lead.name,
            'lead_url': f"{base_url}/odoo/crm/{lead.id}",
        }
