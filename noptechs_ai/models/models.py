# from odoo import models, fields, api


# class noptechs_ai(models.Model):
#     _name = 'noptechs_ai.noptechs_ai'
#     _description = 'noptechs_ai.noptechs_ai'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

