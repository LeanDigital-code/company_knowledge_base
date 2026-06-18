# -*- coding: utf-8 -*-
from odoo import fields, models


class CompanyKnowledgeFavorite(models.Model):
    _name = 'company.knowledge.favorite'
    _description = 'Knowledge Base Favorite'
    _order = 'create_date desc'
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

    _sql_constraints = [
        ('article_user_uniq', 'unique(article_id, user_id)', 'Questo articolo è già nei preferiti dell’utente.'),
    ]
