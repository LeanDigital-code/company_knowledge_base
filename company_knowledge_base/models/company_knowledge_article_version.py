# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CompanyKnowledgeArticleVersion(models.Model):
    _name = 'company.knowledge.article.version'
    _description = 'Knowledge Base Article Version'
    _order = 'article_id, create_date desc, id desc'

    name = fields.Char(string='Nome versione', compute='_compute_name', store=True)
    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    version_number = fields.Integer(string='Numero versione', required=True, default=1)
    title = fields.Char(string='Titolo', required=True)
    summary = fields.Text(string='Descrizione breve')
    article_type = fields.Selection(
        selection=[
            ('procedure', 'Procedura operativa'),
            ('faq', 'FAQ'),
            ('technical_guide', 'Guida tecnica'),
            ('policy', 'Policy aziendale'),
            ('checklist', 'Checklist'),
            ('other', 'Altro'),
        ],
        string='Tipo articolo',
        default='procedure',
    )
    template_id = fields.Many2one('company.knowledge.template', string='Template')
    body_html = fields.Html(string='Contenuto')
    category_id = fields.Many2one('company.knowledge.category', string='Categoria')
    area_id = fields.Many2one('company.knowledge.area', string='Area/Reparto')
    tag_ids = fields.Many2many(
        'company.knowledge.tag',
        'company_knowledge_article_version_tag_rel',
        'version_id',
        'tag_id',
        string='Tag',
    )
    snapshot_state_value = fields.Selection(
        selection=[
            ('draft', 'Bozza'),
            ('review', 'In revisione'),
            ('changes_requested', 'Da modificare'),
            ('approved', 'Approvato'),
            ('published', 'Pubblicato'),
            ('obsolete', 'Obsoleto'),
            ('archived', 'Archiviato'),
        ],
        string='Stato allo snapshot',
        readonly=True,
    )
    review_date = fields.Date(string='Data revisione')
    requires_acknowledgement = fields.Boolean(string='Richiede conferma lettura')
    created_by_id = fields.Many2one(
        'res.users',
        string='Creato da',
        default=lambda self: self.env.user,
        readonly=True,
    )
    change_note = fields.Char(string='Nota modifica')

    @api.depends('article_id.name', 'version_number', 'create_date')
    def _compute_name(self):
        for version in self:
            if version.article_id:
                version.name = '%s - v%s' % (version.article_id.display_name, version.version_number)
            else:
                version.name = _('Versione v%s') % (version.version_number or 1)

    def _check_restore_permission(self):
        if not self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager'):
            raise UserError(_('Solo un Responsabile Knowledge Base può ripristinare una versione precedente.'))

    def action_restore_version(self):
        for version in self:
            version._check_restore_permission()
            article = version.article_id
            article.with_context(no_version_snapshot=True).write({
                'name': version.title,
                'summary': version.summary,
                'article_type': version.article_type,
                'template_id': version.template_id.id,
                'body_html': version.body_html,
                'category_id': version.category_id.id,
                'area_id': version.area_id.id,
                'tag_ids': [(6, 0, version.tag_ids.ids)],
                'review_date': version.review_date,
                'requires_acknowledgement': version.requires_acknowledgement,
                'state': 'draft',
            })
            article._create_version_snapshot(_('Ripristino da %s') % version.display_name)
            article._log_workflow_event('restore_version', version.snapshot_state_value, 'draft', _('Ripristino da %s') % version.display_name)
            article.message_post(body=_('Ripristinata la versione: %s') % version.display_name)
        return True

    def action_compare_with_another_version(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confronta versioni'),
            'res_model': 'company.knowledge.version.compare.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': self._name,
                'active_id': self.id,
                'default_article_id': self.article_id.id,
                'default_left_version_id': self.id,
            },
        }

