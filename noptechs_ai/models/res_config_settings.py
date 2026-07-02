from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Extends the built-in Settings page with a Noptechs AI section.
    The only thing we configure here is which Knowledge folders/articles
    the AI is allowed to read.  We store the IDs as a comma-separated
    string in ir.config_parameter so they survive across sessions.
    """
    _inherit = 'res.config.settings'

    noptechs_ai_knowledge_article_ids = fields.Many2many(
        comodel_name='knowledge.article',
        relation='noptechs_ai_settings_article_rel',   # explicit table name to avoid conflicts
        column1='settings_id',
        column2='article_id',
        string='Accessible Knowledge Folders',
        help=(
            'Select the top-level Knowledge articles/folders the AI may search. '
            'All articles nested inside those folders are also included. '
            'Leave empty to block all Knowledge access.'
        ),
    )

    # -------------------------------------------------------------------------
    # Odoo config-settings contract: get_values / set_values
    # -------------------------------------------------------------------------

    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'noptechs_ai.knowledge_article_ids', default=''
        )
        if param:
            article_ids = [int(x) for x in param.split(',') if x.strip().isdigit()]
            res['noptechs_ai_knowledge_article_ids'] = [(6, 0, article_ids)]
        else:
            res['noptechs_ai_knowledge_article_ids'] = [(5,)]   # clear
        return res

    def set_values(self):
        super().set_values()
        article_ids = self.noptechs_ai_knowledge_article_ids.ids
        self.env['ir.config_parameter'].sudo().set_param(
            'noptechs_ai.knowledge_article_ids',
            ','.join(str(i) for i in article_ids),
        )
