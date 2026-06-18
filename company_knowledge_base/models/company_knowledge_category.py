# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyKnowledgeCategory(models.Model):
    _name = 'company.knowledge.category'
    _description = 'Knowledge Base Category'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'sequence, complete_name'
    _rec_name = 'complete_name'

    name = fields.Char(string='Nome', required=True, translate=True)
    complete_name = fields.Char(
        string='Nome completo',
        compute='_compute_complete_name',
        recursive=True,
        store=True,
    )
    sequence = fields.Integer(string='Sequenza', default=10)
    parent_id = fields.Many2one(
        'company.knowledge.category',
        string='Categoria padre',
        index=True,
        ondelete='restrict',
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'company.knowledge.category',
        'parent_id',
        string='Sottocategorie',
    )
    description = fields.Text(string='Descrizione', translate=True)
    visibility = fields.Selection(
        selection=[
            ('internal', 'Tutti gli utenti interni'),
            ('groups', 'Solo gruppi specifici'),
            ('areas', 'Solo reparti / aree specifiche'),
        ],
        string='Visibilità',
        required=True,
        default='internal',
    )
    allowed_group_ids = fields.Many2many(
        'res.groups',
        'company_knowledge_category_group_rel',
        'category_id',
        'group_id',
        string='Gruppi autorizzati',
        help='Usato solo quando la visibilità è impostata su gruppi specifici.',
    )
    allowed_area_ids = fields.Many2many(
        'company.knowledge.area',
        'company_knowledge_category_area_rel',
        'category_id',
        'area_id',
        string='Aree autorizzate',
        help='Usato solo quando la visibilità è impostata su reparti / aree specifiche.',
    )
    article_count = fields.Integer(
        string='Numero articoli',
        compute='_compute_article_count',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_parent_uniq', 'unique(name, parent_id)', 'Esiste già una categoria con questo nome nello stesso livello.'),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_article_count(self):
        grouped = self.env['company.knowledge.article'].read_group(
            [('category_id', 'in', self.ids)],
            ['category_id'],
            ['category_id'],
        )
        count_by_category = {item['category_id'][0]: item['category_id_count'] for item in grouped}
        for category in self:
            category.article_count = count_by_category.get(category.id, 0)

    @api.constrains('visibility', 'allowed_group_ids', 'allowed_area_ids')
    def _check_visibility_groups(self):
        for category in self:
            if category.visibility == 'groups' and not category.allowed_group_ids:
                raise ValidationError(_('Per una categoria riservata devi indicare almeno un gruppo autorizzato.'))
            if category.visibility == 'areas' and not category.allowed_area_ids:
                raise ValidationError(_('Per una categoria riservata ad aree/reparti devi indicare almeno un’area autorizzata.'))

    def action_open_articles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articoli - %s') % self.display_name,
            'res_model': 'company.knowledge.article',
            'view_mode': 'list,kanban,form',
            'domain': [('category_id', 'child_of', self.id)],
            'context': {'default_category_id': self.id},
        }
