# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyKnowledgeArea(models.Model):
    _name = 'company.knowledge.area'
    _description = 'Knowledge Base Area / Reparto'
    _order = 'sequence, name'

    name = fields.Char(string='Nome area/reparto', required=True, translate=True)
    code = fields.Char(string='Codice')
    sequence = fields.Integer(string='Sequenza', default=10)
    description = fields.Text(string='Descrizione', translate=True)
    user_ids = fields.Many2many(
        'res.users',
        'company_knowledge_area_user_rel',
        'area_id',
        'user_id',
        string='Utenti dell’area',
        help='Utenti che possono leggere contenuti riservati a questa area.',
    )
    manager_ids = fields.Many2many(
        'res.users',
        'company_knowledge_area_manager_rel',
        'area_id',
        'user_id',
        string='Responsabili area',
        help='Responsabili funzionali dell’area. Il ruolo di sicurezza Odoo resta gestito dai gruppi del modulo.',
    )
    category_ids = fields.Many2many(
        'company.knowledge.category',
        'company_knowledge_category_area_rel',
        'area_id',
        'category_id',
        string='Categorie collegate',
    )
    article_ids = fields.One2many('company.knowledge.article', 'area_id', string='Articoli principali')
    article_count = fields.Integer(string='Articoli', compute='_compute_article_count')
    user_count = fields.Integer(string='Utenti', compute='_compute_user_count')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Esiste già un reparto/area con questo nome.'),
        ('code_uniq', 'unique(code)', 'Esiste già un reparto/area con questo codice.'),
    ]

    @api.depends('article_ids')
    def _compute_article_count(self):
        grouped = self.env['company.knowledge.article'].read_group(
            [('area_id', 'in', self.ids)], ['area_id'], ['area_id']
        )
        counts = {row['area_id'][0]: row['area_id_count'] for row in grouped}
        for area in self:
            area.article_count = counts.get(area.id, 0)

    @api.depends('user_ids')
    def _compute_user_count(self):
        for area in self:
            area.user_count = len(area.user_ids)

    @api.constrains('user_ids', 'manager_ids')
    def _check_managers_are_users(self):
        for area in self:
            missing = area.manager_ids - area.user_ids
            if missing:
                raise ValidationError(_(
                    'I responsabili area devono essere inclusi anche tra gli utenti dell’area: %s'
                ) % ', '.join(missing.mapped('display_name')))

    def action_open_articles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articoli - %s') % self.display_name,
            'res_model': 'company.knowledge.article',
            'view_mode': 'list,kanban,form,pivot,graph',
            'domain': ['|', ('area_id', '=', self.id), ('allowed_area_ids', 'in', [self.id])],
            'context': {'default_area_id': self.id},
        }
