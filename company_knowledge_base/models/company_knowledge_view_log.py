# -*- coding: utf-8 -*-
from odoo import fields, models


class CompanyKnowledgeViewLog(models.Model):
    _name = 'company.knowledge.view.log'
    _description = 'Knowledge Base Article View Log'
    _order = 'last_viewed_on desc, create_date desc'
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
    last_viewed_on = fields.Datetime(string='Ultima lettura', required=True, default=fields.Datetime.now)
    view_count = fields.Integer(string='Numero letture', default=1)

    _sql_constraints = [
        ('article_user_view_uniq', 'unique(article_id, user_id)', 'Esiste già un registro lettura per questo articolo e utente.'),
        ('view_count_positive', 'CHECK(view_count >= 0)', 'Il numero di letture non può essere negativo.'),
    ]
