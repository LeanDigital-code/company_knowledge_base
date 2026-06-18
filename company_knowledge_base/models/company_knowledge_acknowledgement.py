# -*- coding: utf-8 -*-
from odoo import fields, models


class CompanyKnowledgeAcknowledgement(models.Model):
    _name = 'company.knowledge.acknowledgement'
    _description = 'Knowledge Base Reading Acknowledgement'
    _order = 'acknowledged_on desc, id desc'
    _rec_name = 'article_id'

    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Utente',
        default=lambda self: self.env.user,
        required=True,
        ondelete='cascade',
        index=True,
    )
    acknowledged_on = fields.Datetime(string='Confermato il', required=True, default=fields.Datetime.now)
    note = fields.Char(string='Nota')

    _sql_constraints = [
        ('article_user_ack_uniq', 'unique(article_id, user_id)', 'L’utente ha già confermato la lettura di questo articolo.'),
    ]
