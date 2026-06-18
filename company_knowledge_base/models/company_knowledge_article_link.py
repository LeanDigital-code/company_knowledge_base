# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyKnowledgeArticleLink(models.Model):
    _name = 'company.knowledge.article.link'
    _description = 'Knowledge Base Related Article'
    _order = 'article_id, sequence, relation_type, related_article_id'
    _rec_name = 'name'

    name = fields.Char(string='Nome collegamento', compute='_compute_name', store=True)
    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo origine',
        required=True,
        ondelete='cascade',
        index=True,
    )
    related_article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo collegato',
        required=True,
        ondelete='cascade',
        index=True,
    )
    relation_type = fields.Selection(
        selection=[
            ('see_also', 'Vedi anche'),
            ('prerequisite', 'Prerequisito'),
            ('next_step', 'Step successivo'),
            ('complements', 'Completa'),
            ('replaces', 'Sostituisce'),
            ('replaced_by', 'Sostituito da'),
            ('duplicate', 'Duplicato / simile'),
        ],
        string='Tipo relazione',
        required=True,
        default='see_also',
    )
    sequence = fields.Integer(string='Sequenza', default=10)
    note = fields.Char(string='Nota')
    related_state = fields.Selection(related='related_article_id.state', string='Stato articolo collegato', readonly=True)
    related_category_id = fields.Many2one(related='related_article_id.category_id', string='Categoria articolo collegato', readonly=True)
    related_quality_score = fields.Integer(related='related_article_id.quality_score', string='Qualità articolo collegato', readonly=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('article_related_article_uniq', 'unique(article_id, related_article_id, relation_type)', 'Questo collegamento tra articoli esiste già con lo stesso tipo relazione.'),
        ('article_not_self', 'CHECK(article_id IS NULL OR related_article_id IS NULL OR article_id <> related_article_id)', 'Un articolo non può essere collegato a se stesso.'),
    ]

    @api.depends('article_id.name', 'related_article_id.name', 'relation_type')
    def _compute_name(self):
        labels = dict(self._fields['relation_type'].selection)
        for link in self:
            if link.article_id and link.related_article_id:
                link.name = '%s → %s (%s)' % (
                    link.article_id.display_name,
                    link.related_article_id.display_name,
                    labels.get(link.relation_type, link.relation_type),
                )
            else:
                link.name = _('Collegamento articolo')

    @api.constrains('article_id', 'related_article_id')
    def _check_article_not_self(self):
        for link in self:
            if link.article_id and link.related_article_id and link.article_id == link.related_article_id:
                raise ValidationError(_('Un articolo non può essere collegato a se stesso.'))

    def action_open_related_article(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.related_article_id.display_name,
            'res_model': 'company.knowledge.article',
            'res_id': self.related_article_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_reverse_link(self):
        inverse_map = {
            'see_also': 'see_also',
            'prerequisite': 'next_step',
            'next_step': 'prerequisite',
            'complements': 'complements',
            'replaces': 'replaced_by',
            'replaced_by': 'replaces',
            'duplicate': 'duplicate',
        }
        Link = self.env['company.knowledge.article.link']
        created = 0
        for link in self:
            inverse_type = inverse_map.get(link.relation_type, 'see_also')
            existing = Link.search([
                ('article_id', '=', link.related_article_id.id),
                ('related_article_id', '=', link.article_id.id),
                ('relation_type', '=', inverse_type),
            ], limit=1)
            if existing:
                continue
            Link.create({
                'article_id': link.related_article_id.id,
                'related_article_id': link.article_id.id,
                'relation_type': inverse_type,
                'sequence': link.sequence,
                'note': link.note or _('Collegamento inverso creato automaticamente.'),
            })
            created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Collegamenti inversi'),
                'message': _('Collegamenti inversi creati: %s') % created,
                'type': 'success',
                'sticky': False,
            },
        }
