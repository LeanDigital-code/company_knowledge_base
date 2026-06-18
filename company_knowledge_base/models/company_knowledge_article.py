# -*- coding: utf-8 -*-
import re
from html import unescape

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class CompanyKnowledgeArticle(models.Model):
    _name = 'company.knowledge.article'
    _description = 'Knowledge Base Article'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, write_date desc, name'
    _mail_post_access = 'read'

    name = fields.Char(string='Titolo', required=True, translate=True, tracking=True)
    summary = fields.Text(string='Descrizione breve', translate=True, tracking=True)
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
        tracking=True,
    )
    template_id = fields.Many2one(
        'company.knowledge.template',
        string='Template',
        tracking=True,
        help='Template usato per impostare struttura, categoria e tag iniziali dell’articolo.',
    )
    body_html = fields.Html(string='Contenuto', sanitize=True, translate=True)
    category_id = fields.Many2one(
        'company.knowledge.category',
        string='Categoria',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    tag_ids = fields.Many2many(
        'company.knowledge.tag',
        'company_knowledge_article_tag_rel',
        'article_id',
        'tag_id',
        string='Tag',
    )
    author_id = fields.Many2one(
        'res.users',
        string='Autore',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        tracking=True,
    )
    owner_id = fields.Many2one(
        'res.users',
        string='Responsabile contenuto',
        default=lambda self: self.env.user,
        tracking=True,
        help='Utente responsabile dell’aggiornamento periodico dell’articolo.',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Bozza'),
            ('review', 'In revisione'),
            ('changes_requested', 'Da modificare'),
            ('approved', 'Approvato'),
            ('published', 'Pubblicato'),
            ('obsolete', 'Obsoleto'),
            ('archived', 'Archiviato'),
        ],
        string='Stato',
        default='draft',
        required=True,
        tracking=True,
    )
    visibility = fields.Selection(
        selection=[
            ('internal', 'Tutti gli utenti interni'),
            ('groups', 'Solo gruppi specifici'),
            ('users', 'Solo utenti specifici'),
            ('areas', 'Solo reparti / aree specifiche'),
            ('portal', 'Pubblico/portale esterno'),
        ],
        string='Visibilità',
        required=True,
        default='internal',
        tracking=True,
    )
    allowed_group_ids = fields.Many2many(
        'res.groups',
        'company_knowledge_article_group_rel',
        'article_id',
        'group_id',
        string='Gruppi autorizzati',
        help='Usato solo quando la visibilità è impostata su gruppi specifici.',
    )
    allowed_user_ids = fields.Many2many(
        'res.users',
        'company_knowledge_article_user_rel',
        'article_id',
        'user_id',
        string='Utenti autorizzati',
        help='Usato solo quando la visibilità è impostata su utenti specifici.',
    )
    area_id = fields.Many2one(
        'company.knowledge.area',
        string='Area/Reparto principale',
        tracking=True,
        help='Area o reparto principalmente responsabile del contenuto.',
    )
    allowed_area_ids = fields.Many2many(
        'company.knowledge.area',
        'company_knowledge_article_area_rel',
        'article_id',
        'area_id',
        string='Aree autorizzate',
        help='Usato solo quando la visibilità è impostata su reparti / aree specifiche.',
    )
    portal_visible = fields.Boolean(
        string='Pubblicato sul portale',
        compute='_compute_portal_fields',
        store=True,
        help='Indica se l’articolo è visibile nella pagina pubblica della knowledge base.',
    )
    portal_url = fields.Char(string='URL portale', compute='_compute_portal_fields')
    version_number = fields.Integer(string='Versione pubblicata/corrente', default=1, readonly=True, copy=False)
    version_ids = fields.One2many('company.knowledge.article.version', 'article_id', string='Storico versioni')
    version_count = fields.Integer(string='Versioni', compute='_compute_version_count')
    feedback_ids = fields.One2many('company.knowledge.feedback', 'article_id', string='Feedback')
    feedback_count = fields.Integer(string='Feedback', compute='_compute_feedback_metrics')
    feedback_todo_count = fields.Integer(string='Feedback aperti', compute='_compute_feedback_metrics')
    feedback_critical_count = fields.Integer(string='Feedback critici', compute='_compute_feedback_metrics')
    rating_avg = fields.Float(string='Valutazione media', compute='_compute_feedback_metrics', digits=(16, 2))
    quality_score = fields.Integer(
        string='Qualità',
        compute='_compute_quality_metrics',
        store=True,
        help='Punteggio di completezza del contenuto da 0 a 100.',
    )
    quality_level = fields.Selection(
        selection=[
            ('excellent', 'Ottima'),
            ('good', 'Buona'),
            ('warning', 'Da migliorare'),
            ('critical', 'Critica'),
        ],
        string='Livello qualità',
        compute='_compute_quality_metrics',
        store=True,
    )
    quality_issue_count = fields.Integer(
        string='Problemi qualità',
        compute='_compute_quality_metrics',
        store=True,
    )
    quality_issue_summary = fields.Text(
        string='Controlli qualità',
        compute='_compute_quality_metrics',
        store=True,
        help='Elenco sintetico degli elementi mancanti o migliorabili secondo template e impostazioni.',
    )
    favorite_ids = fields.One2many('company.knowledge.favorite', 'article_id', string='Preferiti')
    favorite_count = fields.Integer(string='Preferiti', compute='_compute_favorite_metrics')
    is_favorite = fields.Boolean(string='Nei miei preferiti', compute='_compute_favorite_metrics')
    subscription_ids = fields.One2many('company.knowledge.subscription', 'article_id', string='Utenti iscritti')
    subscriber_count = fields.Integer(string='Utenti iscritti', compute='_compute_subscription_metrics')
    is_subscribed_by_me = fields.Boolean(string='Seguito da me', compute='_compute_subscription_metrics')
    notification_log_ids = fields.One2many('company.knowledge.notification.log', 'article_id', string='Notifiche inviate')
    notification_count = fields.Integer(string='Notifiche', compute='_compute_notification_count')
    view_log_ids = fields.One2many('company.knowledge.view.log', 'article_id', string='Registro letture')
    view_log_count = fields.Integer(string='Utenti lettori', compute='_compute_view_log_metrics')
    last_viewed_by_me_on = fields.Datetime(string='Mia ultima lettura', compute='_compute_view_log_metrics')
    related_record_ids = fields.One2many('company.knowledge.article.related', 'article_id', string='Record collegati')
    related_record_count = fields.Integer(string='Record collegati', compute='_compute_related_record_count')
    related_article_link_ids = fields.One2many(
        'company.knowledge.article.link',
        'article_id',
        string='Articoli correlati',
        help='Collegamenti espliciti verso altri articoli Knowledge Base.',
    )
    incoming_article_link_ids = fields.One2many(
        'company.knowledge.article.link',
        'related_article_id',
        string='Citato da articoli',
        readonly=True,
    )
    article_link_count = fields.Integer(string='Articoli correlati', compute='_compute_article_link_metrics')
    incoming_article_link_count = fields.Integer(string='Citato da', compute='_compute_article_link_metrics')
    workflow_log_ids = fields.One2many('company.knowledge.workflow.log', 'article_id', string='Storico workflow')
    workflow_log_count = fields.Integer(string='Eventi workflow', compute='_compute_workflow_log_count')
    acknowledgement_ids = fields.One2many('company.knowledge.acknowledgement', 'article_id', string='Conferme lettura')
    acknowledgement_count = fields.Integer(string='Conferme lettura', compute='_compute_acknowledgement_metrics')
    requires_acknowledgement = fields.Boolean(string='Richiede conferma lettura', tracking=True)
    is_acknowledged_by_me = fields.Boolean(string='Confermato da me', compute='_compute_acknowledgement_metrics')
    acknowledged_by_me_on = fields.Datetime(string='Mia conferma lettura', compute='_compute_acknowledgement_metrics')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'company_knowledge_article_attachment_rel',
        'article_id',
        'attachment_id',
        string='Allegati',
        help='Allegati espliciti dell’articolo. Gli allegati del chatter restano comunque disponibili nello storico messaggi.',
    )
    attachment_count = fields.Integer(string='Allegati', compute='_compute_attachment_count')
    review_date = fields.Date(string='Data prossima revisione', tracking=True)
    is_review_due = fields.Boolean(string='Da revisionare', compute='_compute_is_review_due', search='_search_is_review_due')
    published_date = fields.Datetime(string='Data pubblicazione', readonly=True, copy=False)
    approved_date = fields.Datetime(string='Data approvazione', readonly=True, copy=False)
    approver_id = fields.Many2one('res.users', string='Approvato da', readonly=True, copy=False)
    view_count = fields.Integer(string='Visualizzazioni', default=0, readonly=True, copy=False)
    last_viewed_on = fields.Datetime(string='Ultima lettura registrata', readonly=True, copy=False)
    priority = fields.Selection(
        selection=[
            ('0', 'Normale'),
            ('1', 'Importante'),
            ('2', 'Critico'),
        ],
        string='Priorità',
        default='0',
        tracking=True,
    )
    color = fields.Integer(string='Colore')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_category_uniq', 'unique(name, category_id)', 'Esiste già un articolo con questo titolo nella stessa categoria.'),
    ]

    @api.model
    def _strip_html_to_text(self, html_value):
        text = re.sub(r'<[^>]+>', ' ', html_value or '')
        text = unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    @api.model
    def _get_quality_min_score(self):
        value = self.env['ir.config_parameter'].sudo().get_param('company_knowledge_base.quality_min_score', '70')
        try:
            return max(0, min(100, int(value or 70)))
        except (TypeError, ValueError):
            return 70

    def _get_quality_issues(self):
        self.ensure_one()
        issues = []
        body_text = self._strip_html_to_text(self.body_html).lower()
        body_length = len(body_text)
        template = self.template_id
        quality_enabled = not template or template.quality_check_enabled
        if not quality_enabled:
            return issues

        min_length = template.min_body_length if template and template.min_body_length else 120
        if body_length < min_length:
            issues.append(_('Contenuto troppo breve: %s caratteri su %s consigliati.') % (body_length, min_length))
        if template and template.requires_summary and not (self.summary or '').strip():
            issues.append(_('Sintesi breve mancante.'))
        elif not template and not (self.summary or '').strip():
            issues.append(_('Sintesi breve consigliata.'))
        if template and template.requires_tags and not self.tag_ids:
            issues.append(_('Tag obbligatori mancanti.'))
        if template and template.requires_attachments and not self.attachment_ids:
            issues.append(_('Allegati obbligatori mancanti.'))
        if not self.review_date and self.state in ('approved', 'published', 'obsolete'):
            issues.append(_('Data prossima revisione mancante.'))
        if not self.owner_id:
            issues.append(_('Responsabile contenuto mancante.'))

        required_sections = []
        if template and template.required_section_keywords:
            required_sections = [line.strip() for line in template.required_section_keywords.splitlines() if line.strip()]
        for section in required_sections:
            if section.lower() not in body_text:
                issues.append(_('Sezione/parola chiave mancante: %s') % section)
        return issues

    @api.depends(
        'summary', 'body_html', 'tag_ids', 'attachment_ids', 'review_date', 'owner_id', 'state',
        'template_id', 'template_id.quality_check_enabled', 'template_id.min_body_length',
        'template_id.requires_summary', 'template_id.requires_tags', 'template_id.requires_attachments',
        'template_id.required_section_keywords'
    )
    def _compute_quality_metrics(self):
        for article in self:
            issues = article._get_quality_issues() if article.id or article.body_html or article.summary else []
            score = max(0, 100 - (len(issues) * 15))
            if score >= 90:
                level = 'excellent'
            elif score >= 75:
                level = 'good'
            elif score >= 50:
                level = 'warning'
            else:
                level = 'critical'
            article.quality_score = score
            article.quality_level = level
            article.quality_issue_count = len(issues)
            article.quality_issue_summary = '\n'.join('- %s' % issue for issue in issues) if issues else _('Nessun problema rilevato.')

    def _ensure_quality_ready(self):
        min_score = self._get_quality_min_score()
        for article in self:
            if article.quality_score < min_score:
                raise UserError(_(
                    'L’articolo "%s" non raggiunge il punteggio qualità minimo (%s/%s).\n\n%s'
                ) % (article.display_name, article.quality_score, min_score, article.quality_issue_summary or ''))

    def action_check_quality(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Qualità contenuto: %s/100') % self.quality_score,
                'message': self.quality_issue_summary or _('Nessun problema rilevato.'),
                'type': 'success' if self.quality_score >= self._get_quality_min_score() else 'warning',
                'sticky': True,
            },
        }

    @api.depends('version_ids')
    def _compute_version_count(self):
        grouped = self.env['company.knowledge.article.version'].read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        for article in self:
            article.version_count = counts.get(article.id, 0)

    @api.depends('feedback_ids.rating', 'feedback_ids.active', 'feedback_ids.state', 'feedback_ids.feedback_type', 'feedback_ids.severity')
    def _compute_feedback_metrics(self):
        for article in self:
            feedbacks = article.feedback_ids.filtered(lambda feedback: feedback.active)
            open_feedbacks = feedbacks.filtered(lambda feedback: feedback.state == 'todo')
            critical_feedbacks = open_feedbacks.filtered(lambda feedback: feedback.severity in ('high', 'critical') or feedback.feedback_type in ('error', 'obsolete', 'missing'))
            article.feedback_count = len(feedbacks)
            article.feedback_todo_count = len(open_feedbacks)
            article.feedback_critical_count = len(critical_feedbacks)
            ratings = [int(feedback.rating) for feedback in feedbacks if feedback.rating]
            article.rating_avg = sum(ratings) / len(ratings) if ratings else 0.0


    @api.depends('favorite_ids')
    @api.depends_context('uid')
    def _compute_favorite_metrics(self):
        grouped = self.env['company.knowledge.favorite'].sudo().read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        my_favorite_article_ids = set(self.env['company.knowledge.favorite'].sudo().search([
            ('article_id', 'in', self.ids),
            ('user_id', '=', self.env.user.id),
        ]).mapped('article_id').ids)
        for article in self:
            article.favorite_count = counts.get(article.id, 0)
            article.is_favorite = article.id in my_favorite_article_ids

    @api.depends('subscription_ids', 'subscription_ids.active')
    @api.depends_context('uid')
    def _compute_subscription_metrics(self):
        grouped = self.env['company.knowledge.subscription'].sudo().read_group(
            [('article_id', 'in', self.ids), ('active', '=', True)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        my_subscription_article_ids = set(self.env['company.knowledge.subscription'].sudo().search([
            ('article_id', 'in', self.ids),
            ('user_id', '=', self.env.user.id),
            ('active', '=', True),
        ]).mapped('article_id').ids)
        for article in self:
            article.subscriber_count = counts.get(article.id, 0)
            article.is_subscribed_by_me = article.id in my_subscription_article_ids

    @api.depends('notification_log_ids')
    def _compute_notification_count(self):
        grouped = self.env['company.knowledge.notification.log'].sudo().read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        for article in self:
            article.notification_count = counts.get(article.id, 0)

    @api.depends('view_log_ids')
    @api.depends_context('uid')
    def _compute_view_log_metrics(self):
        grouped = self.env['company.knowledge.view.log'].sudo().read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        my_logs = self.env['company.knowledge.view.log'].sudo().search([
            ('article_id', 'in', self.ids),
            ('user_id', '=', self.env.user.id),
        ])
        my_last_viewed = {log.article_id.id: log.last_viewed_on for log in my_logs}
        for article in self:
            article.view_log_count = counts.get(article.id, 0)
            article.last_viewed_by_me_on = my_last_viewed.get(article.id)

    @api.depends('related_record_ids')
    def _compute_related_record_count(self):
        grouped = self.env['company.knowledge.article.related'].sudo().read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        for article in self:
            article.related_record_count = counts.get(article.id, 0)

    @api.depends('related_article_link_ids', 'incoming_article_link_ids')
    def _compute_article_link_metrics(self):
        Link = self.env['company.knowledge.article.link'].sudo()
        outgoing_grouped = Link.read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        incoming_grouped = Link.read_group(
            [('related_article_id', 'in', self.ids)],
            ['related_article_id'],
            ['related_article_id'],
        )
        outgoing_counts = {
            row['article_id'][0]: row.get('article_id_count', 0)
            for row in outgoing_grouped
            if row.get('article_id')
        }
        incoming_counts = {
            row['related_article_id'][0]: row.get('related_article_id_count', 0)
            for row in incoming_grouped
            if row.get('related_article_id')
        }
        for article in self:
            article.article_link_count = outgoing_counts.get(article.id, 0)
            article.incoming_article_link_count = incoming_counts.get(article.id, 0)

    @api.depends('workflow_log_ids')
    def _compute_workflow_log_count(self):
        grouped = self.env['company.knowledge.workflow.log'].sudo().read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        for article in self:
            article.workflow_log_count = counts.get(article.id, 0)

    @api.depends('acknowledgement_ids', 'acknowledgement_ids.user_id', 'acknowledgement_ids.acknowledged_on')
    @api.depends_context('uid')
    def _compute_acknowledgement_metrics(self):
        grouped = self.env['company.knowledge.acknowledgement'].sudo().read_group(
            [('article_id', 'in', self.ids)],
            ['article_id'],
            ['article_id'],
        )
        counts = {row['article_id'][0]: row['article_id_count'] for row in grouped}
        my_acks = self.env['company.knowledge.acknowledgement'].sudo().search([
            ('article_id', 'in', self.ids),
            ('user_id', '=', self.env.user.id),
        ])
        my_ack_dates = {ack.article_id.id: ack.acknowledged_on for ack in my_acks}
        for article in self:
            article.acknowledgement_count = counts.get(article.id, 0)
            article.is_acknowledged_by_me = article.id in my_ack_dates
            article.acknowledged_by_me_on = my_ack_dates.get(article.id)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for article in self:
            article.attachment_count = len(article.attachment_ids)

    @api.depends('state', 'visibility')
    def _compute_portal_fields(self):
        base_path = '/company_knowledge/article/%s'
        for article in self:
            article.portal_visible = bool(article.state == 'published' and article.visibility == 'portal')
            article.portal_url = base_path % article.id if article.id and article.portal_visible else False

    @api.onchange('template_id')
    def _onchange_template_id(self):
        for article in self:
            template = article.template_id
            if not template:
                continue
            article.article_type = template.article_type
            if template.category_id and not article.category_id:
                article.category_id = template.category_id
            if template.tag_ids:
                article.tag_ids = [(6, 0, template.tag_ids.ids)]
            if template.summary and not article.summary:
                article.summary = template.summary
            if template.body_html and not article.body_html:
                article.body_html = template.body_html

    @api.depends('review_date', 'state')
    def _compute_is_review_due(self):
        today = fields.Date.context_today(self)
        for article in self:
            article.is_review_due = bool(
                article.review_date
                and article.review_date <= today
                and article.state in ('published', 'approved', 'obsolete')
            )

    def _search_is_review_due(self, operator, value):
        today = fields.Date.context_today(self)
        positive_domain = [
            ('review_date', '<=', today),
            ('state', 'in', ['published', 'approved', 'obsolete']),
        ]
        negative_domain = [
            '|',
            ('review_date', '=', False),
            '|',
            ('review_date', '>', today),
            ('state', 'not in', ['published', 'approved', 'obsolete']),
        ]
        if (operator in ('=', '==') and value) or (operator in ('!=', '<>') and not value):
            return positive_domain
        return negative_domain

    @api.constrains('visibility', 'allowed_group_ids', 'allowed_user_ids', 'allowed_area_ids')
    def _check_visibility_recipients(self):
        for article in self:
            if article.visibility == 'groups' and not article.allowed_group_ids:
                raise ValidationError(_('Per un articolo riservato a gruppi devi indicare almeno un gruppo autorizzato.'))
            if article.visibility == 'users' and not article.allowed_user_ids:
                raise ValidationError(_('Per un articolo riservato a utenti specifici devi indicare almeno un utente autorizzato.'))
            if article.visibility == 'areas' and not article.allowed_area_ids:
                raise ValidationError(_('Per un articolo riservato ad aree/reparti devi indicare almeno un’area autorizzata.'))
            if article.visibility == 'portal' and article.state not in ('draft', 'review', 'changes_requested', 'approved', 'published', 'obsolete', 'archived'):
                raise ValidationError(_('Stato articolo non valido per la pubblicazione su portale.'))

    @api.constrains('body_html', 'state')
    def _check_published_content(self):
        for article in self:
            if article.state in ('approved', 'published') and not article.body_html:
                raise ValidationError(_('Un articolo approvato o pubblicato deve avere un contenuto.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('no_version_snapshot'):
            for article in records:
                article._create_version_snapshot(_('Creazione articolo'))
                article._log_workflow_event('create', False, article.state, _('Creazione articolo'))
        return records

    def write(self, vals):
        tracked_fields = {'name', 'summary', 'body_html', 'category_id', 'tag_ids', 'article_type', 'template_id', 'review_date', 'requires_acknowledgement', 'attachment_ids', 'allowed_user_ids', 'allowed_area_ids', 'area_id', 'visibility', 'related_article_link_ids'}
        create_snapshot = bool(tracked_fields.intersection(vals.keys())) and not self.env.context.get('no_version_snapshot')
        published_before = self.filtered(lambda article: article.state == 'published')
        result = super().write(vals)
        if create_snapshot:
            for article in self:
                article._create_version_snapshot(_('Modifica contenuto'))
        update_fields = tracked_fields.intersection(vals.keys()) - {'requires_acknowledgement'}
        auto_notify = self.env['ir.config_parameter'].sudo().get_param('company_knowledge_base.auto_notify_on_update', 'False') == 'True'
        if update_fields and auto_notify and not self.env.context.get('suppress_knowledge_auto_notify'):
            published_before._notify_users(
                notification_type='update',
                message=_('<p>L’articolo <strong>%s</strong> è stato aggiornato.</p>') % ', '.join(published_before.mapped('display_name')),
                include_audience=False,
                create_logs=True,
            )
        return result

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': _('%s (copia)') % self.name,
            'state': 'draft',
            'published_date': False,
            'approved_date': False,
            'approver_id': False,
            'version_number': 1,
            'view_count': 0,
            'last_viewed_on': False,
        })
        return super().copy(default)

    def unlink(self):
        restricted = self.filtered(lambda article: article.state in ('published', 'approved'))
        if restricted and not self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager'):
            raise UserError(_('Solo un Responsabile può eliminare articoli approvati o pubblicati. Usa Archivia per mantenerne lo storico.'))
        return super().unlink()

    def _create_version_snapshot(self, change_note=False):
        Version = self.env['company.knowledge.article.version'].sudo()
        for article in self:
            Version.create({
                'article_id': article.id,
                'version_number': article.version_number or 1,
                'title': article.name,
                'summary': article.summary,
                'article_type': article.article_type,
                'template_id': article.template_id.id,
                'body_html': article.body_html,
                'category_id': article.category_id.id,
                'area_id': article.area_id.id,
                'tag_ids': [(6, 0, article.tag_ids.ids)],
                'snapshot_state_value': article.state,
                'review_date': article.review_date,
                'requires_acknowledgement': article.requires_acknowledgement,
                'created_by_id': self.env.user.id,
                'change_note': change_note or '',
            })

    def _log_workflow_event(self, action, from_state=False, to_state=False, note=False):
        Log = self.env['company.knowledge.workflow.log'].sudo()
        for article in self:
            Log.create({
                'article_id': article.id,
                'action': action or 'other',
                'from_state': from_state or False,
                'to_state': to_state or article.state,
                'note': note or '',
                'user_id': self.env.user.id,
            })

    def _get_visibility_target_users(self):
        self.ensure_one()
        users = self.env['res.users']
        if self.visibility == 'groups':
            for group in self.allowed_group_ids:
                users |= group.users
        elif self.visibility == 'users':
            users |= self.allowed_user_ids
        elif self.visibility == 'areas':
            users |= self.allowed_area_ids.mapped('user_ids')
        elif self.visibility == 'internal':
            group = self.env.ref('company_knowledge_base.group_company_knowledge_user', raise_if_not_found=False)
            if group:
                users |= group.users
        users |= self.author_id | self.owner_id
        return users.filtered(lambda user: user.active and user.partner_id and user.has_group('base.group_user'))

    def _notify_users(self, notification_type='custom', message=False, include_audience=False, create_logs=True):
        Log = self.env['company.knowledge.notification.log'].sudo()
        now = fields.Datetime.now()
        for article in self:
            users = self.env['company.knowledge.subscription'].sudo().search([('article_id', '=', article.id), ('active', '=', True)]).mapped('user_id')
            if include_audience:
                users |= article._get_visibility_target_users()
            users = users.filtered(lambda user: user.active and user.partner_id and user.has_group('base.group_user'))
            if not users:
                continue
            body = message or _('<p>Aggiornamento disponibile per l’articolo <strong>%s</strong>.</p>') % article.display_name
            article.message_post(
                body=body,
                partner_ids=users.mapped('partner_id').ids,
                subtype_xmlid='mail.mt_comment',
            )
            if create_logs:
                Log.create([{
                    'article_id': article.id,
                    'user_id': user.id,
                    'sent_by_id': self.env.user.id,
                    'sent_on': now,
                    'notification_type': notification_type,
                    'message': body,
                } for user in users])
            self.env['company.knowledge.subscription'].sudo().search([('article_id', '=', article.id), ('user_id', 'in', users.ids), ('active', '=', True)]).write({'last_notified_on': now})
        return True

    def _schedule_review_activity_if_needed(self):
        Activity = self.env['mail.activity'].sudo()
        IrModel = self.env['ir.model'].sudo()
        model_id = IrModel._get_id(self._name)
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return 0
        created = 0
        for article in self:
            if not article.owner_id or not article.review_date:
                continue
            existing = Activity.search([
                ('res_model_id', '=', model_id),
                ('res_id', '=', article.id),
                ('activity_type_id', '=', activity_type.id),
                ('user_id', '=', article.owner_id.id),
                ('summary', '=', _('Revisione articolo knowledge base')),
            ], limit=1)
            if existing:
                continue
            article.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=article.review_date,
                summary=_('Revisione articolo knowledge base'),
                note=_('Verificare e aggiornare l’articolo: %s') % article.display_name,
                user_id=article.owner_id.id,
            )
            created += 1
        return created

    @api.model
    def _cron_schedule_review_activities(self):
        Param = self.env['ir.config_parameter'].sudo()
        enabled = Param.get_param('company_knowledge_base.review_activity_enabled', 'True')
        if str(enabled).lower() in ('0', 'false', 'no'):
            return 0
        try:
            days_before = int(Param.get_param('company_knowledge_base.review_activity_days_before', '7') or 7)
        except ValueError:
            days_before = 7
        today = fields.Date.context_today(self)
        deadline = fields.Date.add(today, days=max(days_before, 0))
        articles = self.search([
            ('review_date', '!=', False),
            ('review_date', '<=', deadline),
            ('state', 'in', ['published', 'approved', 'obsolete']),
            ('owner_id', '!=', False),
        ])
        return articles._schedule_review_activity_if_needed()

    def _check_editor_permission(self):
        if not (
            self.env.user.has_group('company_knowledge_base.group_company_knowledge_editor')
            or self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager')
        ):
            raise UserError(_('Solo Editor o Responsabili Knowledge Base possono eseguire questa operazione.'))

    def _check_manager_permission(self):
        if not self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager'):
            raise UserError(_('Solo un Responsabile Knowledge Base può eseguire questa operazione.'))

    def action_send_review(self):
        self._check_editor_permission()
        for article in self:
            if article.state not in ('draft', 'changes_requested'):
                raise UserError(_('Puoi inviare in revisione solo articoli in Bozza o Da modificare.'))
            if not article.body_html:
                raise UserError(_('Inserisci il contenuto dell’articolo prima di inviarlo in revisione.'))
            enforce_quality = self.env['ir.config_parameter'].sudo().get_param('company_knowledge_base.enforce_quality_on_review', 'False') == 'True'
            if enforce_quality:
                article._ensure_quality_ready()
            old_state = article.state
            article.write({'state': 'review'})
            article._log_workflow_event('submit_review', old_state, 'review', _('Articolo inviato in revisione.'))
            article.message_post(body=_('Articolo inviato in revisione.'))
        return True

    def action_request_changes(self, note=False):
        self._check_manager_permission()
        for article in self:
            if article.state != 'review':
                raise UserError(_('Puoi richiedere modifiche solo per articoli in revisione.'))
            old_state = article.state
            article.write({'state': 'changes_requested'})
            article._log_workflow_event('request_changes', old_state, 'changes_requested', note or _('Richieste modifiche sull’articolo.'))
            article.message_post(body=_('Richieste modifiche sull’articolo.') + (('<br/><b>%s</b><br/>%s' % (_('Motivazione:'), note)) if note else ''))
        return True

    def action_open_request_changes_wizard(self):
        self.ensure_one()
        self._check_manager_permission()
        if self.state != 'review':
            raise UserError(_('Puoi richiedere modifiche solo per articoli in revisione.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Richiedi modifiche'),
            'res_model': 'company.knowledge.review.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_article_id': self.id,
                'default_action_type': 'request_changes',
            },
        }

    def action_approve(self):
        self._check_manager_permission()
        for article in self:
            if article.state not in ('review', 'changes_requested'):
                raise UserError(_('Puoi approvare solo articoli in revisione o da modificare.'))
            old_state = article.state
            article.write({
                'state': 'approved',
                'approved_date': fields.Datetime.now(),
                'approver_id': self.env.user.id,
            })
            article._log_workflow_event('approve', old_state, 'approved', _('Articolo approvato.'))
            article.message_post(body=_('Articolo approvato.'))
        return True

    def action_publish(self):
        self._check_manager_permission()
        for article in self:
            if article.state != 'approved':
                raise UserError(_('Solo gli articoli approvati possono essere pubblicati.'))
            enforce_quality = self.env['ir.config_parameter'].sudo().get_param('company_knowledge_base.enforce_quality_on_review', 'False') == 'True'
            if enforce_quality:
                article._ensure_quality_ready()
            new_version = article.version_number
            if article.published_date:
                new_version += 1
            old_state = article.state
            article.with_context(no_version_snapshot=True).write({
                'state': 'published',
                'published_date': fields.Datetime.now(),
                'version_number': new_version,
            })
            article._create_version_snapshot(_('Pubblicazione v%s') % new_version)
            article._log_workflow_event('publish', old_state, 'published', _('Articolo pubblicato come versione %s.') % new_version)
            article.message_post(body=_('Articolo pubblicato come versione %s.') % new_version)
            auto_notify = self.env['ir.config_parameter'].sudo().get_param('company_knowledge_base.auto_notify_on_publish', 'False') == 'True'
            if auto_notify:
                article._notify_users(
                    notification_type='publish',
                    message=_('<p>È stato pubblicato l’articolo <strong>%s</strong>.</p>') % article.display_name,
                    include_audience=True,
                    create_logs=True,
                )
        return True

    def action_new_revision(self):
        self._check_editor_permission()
        is_manager = self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager')
        for article in self:
            if article.state not in ('published', 'obsolete'):
                raise UserError(_('Puoi aprire una nuova revisione solo da articoli pubblicati o obsoleti.'))
            if not is_manager and article.author_id != self.env.user and article.owner_id != self.env.user:
                raise UserError(_('Puoi aprire una nuova revisione solo per articoli creati da te o assegnati a te.'))
            old_state = article.state
            article.sudo().with_context(no_version_snapshot=True).write({'state': 'draft'})
            article._log_workflow_event('new_revision', old_state, 'draft', _('Nuova revisione aperta.'))
            article.message_post(body=_('Nuova revisione aperta. La versione pubblicata precedente resta nello storico.'))
        return True

    def action_mark_obsolete(self):
        self._check_manager_permission()
        for article in self:
            if article.state != 'published':
                raise UserError(_('Puoi marcare come obsoleto solo un articolo pubblicato.'))
            old_state = article.state
            article.write({'state': 'obsolete'})
            article._log_workflow_event('obsolete', old_state, 'obsolete', _('Articolo marcato come obsoleto.'))
            article.message_post(body=_('Articolo marcato come obsoleto.'))
        return True

    def action_archive_article(self):
        self._check_manager_permission()
        for article in self:
            old_state = article.state
            article.with_context(no_version_snapshot=True).write({
                'state': 'archived',
                'active': False,
            })
            article._log_workflow_event('archive', old_state, 'archived', _('Articolo archiviato.'))
            article.message_post(body=_('Articolo archiviato.'))
        return True

    def action_reset_draft(self):
        self._check_editor_permission()
        for article in self:
            old_state = article.state
            article.write({'state': 'draft'})
            article._log_workflow_event('reset_draft', old_state, 'draft', _('Articolo riportato in bozza.'))
            article.message_post(body=_('Articolo riportato in bozza.'))
        return True

    def action_register_view(self):
        ViewLog = self.env['company.knowledge.view.log'].sudo()
        now = fields.Datetime.now()
        for article in self:
            article.sudo().write({
                'view_count': article.view_count + 1,
                'last_viewed_on': now,
            })
            log = ViewLog.search([
                ('article_id', '=', article.id),
                ('user_id', '=', self.env.user.id),
            ], limit=1)
            if log:
                log.write({
                    'last_viewed_on': now,
                    'view_count': log.view_count + 1,
                })
            else:
                ViewLog.create({
                    'article_id': article.id,
                    'user_id': self.env.user.id,
                    'last_viewed_on': now,
                    'view_count': 1,
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Lettura registrata'),
                'message': _('La consultazione dell’articolo è stata registrata.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_toggle_favorite(self):
        Favorite = self.env['company.knowledge.favorite'].sudo()
        for article in self:
            favorite = Favorite.search([
                ('article_id', '=', article.id),
                ('user_id', '=', self.env.user.id),
            ], limit=1)
            if favorite:
                favorite.unlink()
                message = _('Articolo rimosso dai preferiti.')
            else:
                Favorite.create({
                    'article_id': article.id,
                    'user_id': self.env.user.id,
                })
                message = _('Articolo aggiunto ai preferiti.')
            article.message_post(body=message)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preferiti aggiornati'),
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_toggle_subscription(self):
        Subscription = self.env['company.knowledge.subscription'].sudo()
        for article in self:
            subscription = Subscription.search([
                ('article_id', '=', article.id),
                ('user_id', '=', self.env.user.id),
            ], limit=1)
            if subscription:
                if subscription.active:
                    subscription.write({'active': False})
                    message = _('Non segui più questo articolo.')
                else:
                    subscription.write({'active': True, 'subscribed_on': fields.Datetime.now()})
                    message = _('Ora segui questo articolo.')
            else:
                Subscription.create({
                    'article_id': article.id,
                    'user_id': self.env.user.id,
                    'notification_level': 'major',
                })
                message = _('Ora segui questo articolo.')
            article.message_post(body=message)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Iscrizioni aggiornate'),
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_open_notify_wizard(self):
        self.ensure_one()
        self._check_manager_permission()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Notifica utenti'),
            'res_model': 'company.knowledge.notify.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': self._name,
                'active_id': self.id,
                'default_article_id': self.id,
            },
        }

    def action_open_subscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Utenti iscritti - %s') % self.display_name,
            'res_model': 'company.knowledge.subscription',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_open_notification_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Notifiche - %s') % self.display_name,
            'res_model': 'company.knowledge.notification.log',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_apply_template(self):
        self._check_editor_permission()
        for article in self:
            template = article.template_id
            if not template:
                raise UserError(_('Seleziona un template prima di applicarlo.'))
            article.write({
                'article_type': template.article_type,
                'category_id': template.category_id.id or article.category_id.id,
                'tag_ids': [(6, 0, template.tag_ids.ids)] if template.tag_ids else [(6, 0, article.tag_ids.ids)],
                'summary': template.summary or article.summary,
                'body_html': template.body_html or article.body_html,
            })
            article.message_post(body=_('Template applicato: %s') % template.display_name)
        return True


    def selection_label(self, field_name):
        self.ensure_one()
        field = self._fields.get(field_name)
        if not field or not getattr(field, 'selection', None):
            return self[field_name] or ''
        return dict(field.selection).get(self[field_name], self[field_name] or '')

    def action_print_pdf(self):
        if not self:
            raise UserError(_('Seleziona almeno un articolo da stampare.'))
        return self.env.ref('company_knowledge_base.action_report_company_knowledge_article_pdf').report_action(self)

    def action_open_export_wizard(self):
        article_ids = self.ids or self.env.context.get('active_ids', [])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Esporta articoli Knowledge Base'),
            'res_model': 'company.knowledge.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_article_ids': [(6, 0, article_ids)]},
        }

    def action_open_compare_versions_wizard(self):
        self.ensure_one()
        if self.version_count < 2:
            raise UserError(_('Servono almeno due versioni per eseguire un confronto.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confronta versioni'),
            'res_model': 'company.knowledge.version.compare.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_article_id': self.id,
            },
        }

    def action_publish_portal(self):
        self._check_manager_permission()
        for article in self:
            if article.state != 'published':
                raise UserError(_('Solo gli articoli pubblicati possono essere resi visibili sul portale.'))
            article.write({'visibility': 'portal'})
            article._log_workflow_event('portal_publish', article.state, article.state, _('Articolo reso visibile sul portale esterno.'))
            article.message_post(body=_('Articolo reso visibile sul portale esterno.'))
        return True

    def action_unpublish_portal(self):
        self._check_manager_permission()
        for article in self:
            if article.visibility != 'portal':
                continue
            article.write({'visibility': 'internal'})
            article._log_workflow_event('portal_unpublish', article.state, article.state, _('Articolo rimosso dal portale esterno.'))
            article.message_post(body=_('Articolo rimosso dal portale esterno.'))
        return True

    def action_open_suggested_articles(self):
        self.ensure_one()
        domain = [('id', '!=', self.id), ('state', '=', 'published')]
        if self.tag_ids:
            domain = ['|', ('tag_ids', 'in', self.tag_ids.ids), ('category_id', 'child_of', self.category_id.id)] + domain
        else:
            domain = [('category_id', 'child_of', self.category_id.id)] + domain
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articoli suggeriti - %s') % self.display_name,
            'res_model': 'company.knowledge.article',
            'view_mode': 'list,kanban,form',
            'domain': domain,
            'context': {'search_default_published': 1},
        }

    def action_open_favorites(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preferiti - %s') % self.display_name,
            'res_model': 'company.knowledge.favorite',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_open_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Letture - %s') % self.display_name,
            'res_model': 'company.knowledge.view.log',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_open_related_records(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Record collegati - %s') % self.display_name,
            'res_model': 'company.knowledge.article.related',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_open_article_links(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articoli correlati - %s') % self.display_name,
            'res_model': 'company.knowledge.article.link',
            'view_mode': 'list,form',
            'domain': ['|', ('article_id', '=', self.id), ('related_article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_create_suggested_article_links(self):
        self._check_editor_permission()
        Link = self.env['company.knowledge.article.link']
        created = 0
        for article in self:
            domain = [('id', '!=', article.id), ('state', '=', 'published'), ('active', '=', True)]
            if article.category_id and article.tag_ids:
                domain = ['|', ('tag_ids', 'in', article.tag_ids.ids), ('category_id', 'child_of', article.category_id.id)] + domain
            elif article.category_id:
                domain = [('category_id', 'child_of', article.category_id.id)] + domain
            elif article.tag_ids:
                domain = [('tag_ids', 'in', article.tag_ids.ids)] + domain
            candidates = self.search(domain, order='view_count desc, quality_score desc, write_date desc', limit=8)
            for target in candidates:
                existing = Link.search([
                    ('article_id', '=', article.id),
                    ('related_article_id', '=', target.id),
                    ('relation_type', '=', 'see_also'),
                ], limit=1)
                if existing:
                    continue
                Link.create({
                    'article_id': article.id,
                    'related_article_id': target.id,
                    'relation_type': 'see_also',
                    'sequence': 10,
                    'note': _('Suggerito automaticamente per categoria o tag.'),
                })
                created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Articoli correlati'),
                'message': _('Collegamenti suggeriti creati: %s') % created,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_open_versions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Versioni - %s') % self.display_name,
            'res_model': 'company.knowledge.article.version',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_open_feedback(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Feedback - %s') % self.display_name,
            'res_model': 'company.knowledge.feedback',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_create_feedback(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nuovo feedback'),
            'res_model': 'company.knowledge.feedback',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_article_id': self.id},
        }

    def action_acknowledge(self):
        Ack = self.env['company.knowledge.acknowledgement'].sudo()
        now = fields.Datetime.now()
        for article in self:
            if article.state != 'published':
                raise UserError(_('Puoi confermare la lettura solo di articoli pubblicati.'))
            if not article.requires_acknowledgement:
                raise UserError(_('Questo articolo non richiede conferma lettura.'))
            existing = Ack.search([
                ('article_id', '=', article.id),
                ('user_id', '=', self.env.user.id),
            ], limit=1)
            if existing:
                raise UserError(_('Hai già confermato la lettura di questo articolo.'))
            Ack.create({
                'article_id': article.id,
                'user_id': self.env.user.id,
                'acknowledged_on': now,
            })
            article.action_register_view()
            article.message_post(body=_('Lettura confermata da %s.') % self.env.user.display_name)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Conferma registrata'),
                'message': _('La tua conferma lettura è stata registrata.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_open_workflow_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Workflow - %s') % self.display_name,
            'res_model': 'company.knowledge.workflow.log',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_open_acknowledgements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Conferme lettura - %s') % self.display_name,
            'res_model': 'company.knowledge.acknowledgement',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_schedule_review_activity(self):
        self._check_manager_permission()
        created = self._schedule_review_activity_if_needed()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Attività revisione'),
                'message': _('Attività create: %s') % created,
                'type': 'success',
                'sticky': False,
            },
        }

    @api.model
    def _get_dashboard_domain(self, category_id=False, query=False, state_filter=False, quick_filter=False):
        """Build the dashboard domain in one place.

        The dashboard needs the same domain for counters, list data and the
        fallback standard Odoo action. This helper keeps filters consistent and
        preserves normal ACLs / record rules because it intentionally does not
        use sudo().
        """
        category_id = int(category_id or 0) or False
        query = (query or '').strip()
        state_filter = state_filter or False
        quick_filter = quick_filter or False

        domain = [('active', '=', True)]
        if state_filter == 'review_pending':
            domain.append(('state', 'in', ['review', 'changes_requested']))
        elif state_filter == 'review_due':
            domain.append(('is_review_due', '=', True))
        elif state_filter:
            domain.append(('state', '=', state_filter))

        if quick_filter == 'favorites':
            domain.append(('favorite_ids.user_id', '=', self.env.user.id))
        elif quick_filter == 'subscribed':
            domain.extend([
                ('subscription_ids.user_id', '=', self.env.user.id),
                ('subscription_ids.active', '=', True),
            ])
        elif quick_filter == 'ack_required':
            domain.extend([
                ('requires_acknowledgement', '=', True),
                ('state', '=', 'published'),
            ])
        elif quick_filter == 'low_quality':
            domain.append(('quality_score', '<', self._get_quality_min_score()))
        elif quick_filter == 'recent':
            domain.append(('view_log_ids.user_id', '=', self.env.user.id))
        elif quick_filter == 'with_attachments':
            domain.append(('attachment_ids', '!=', False))
        elif quick_filter == 'portal':
            domain.append(('portal_visible', '=', True))
        elif quick_filter == 'with_related':
            domain.append(('related_article_link_ids', '!=', False))
        elif quick_filter == 'feedback_todo':
            domain.append(('feedback_ids.state', '=', 'todo'))
        elif quick_filter == 'feedback_critical':
            domain.extend([
                ('feedback_ids.state', '=', 'todo'),
                '|',
                ('feedback_ids.severity', 'in', ['high', 'critical']),
                ('feedback_ids.feedback_type', 'in', ['error', 'obsolete', 'missing']),
            ])

        if category_id:
            domain.append(('category_id', 'child_of', category_id))
        if query:
            domain = expression.AND([
                domain,
                ['|', '|', '|', '|',
                 ('name', 'ilike', query),
                 ('summary', 'ilike', query),
                 ('body_html', 'ilike', query),
                 ('tag_ids.name', 'ilike', query),
                 ('category_id.name', 'ilike', query)],
            ])
        return domain

    @api.model
    def _get_dashboard_order(self, sort_by=False, query=False):
        sort_by = sort_by or ('relevance' if query else 'updated')
        mapping = {
            'updated': 'write_date desc, name asc',
            'created': 'create_date desc, name asc',
            'popular': 'view_count desc, write_date desc, name asc',
            'title': 'name asc',
            'quality': 'quality_score asc, write_date desc, name asc',
            'review_date': 'review_date asc, write_date desc, name asc',
            'recent': 'write_date desc, name asc',
            'relevance': 'priority desc, write_date desc, name asc',
        }
        return mapping.get(sort_by, mapping['updated'])

    @api.model
    def _dashboard_query_terms(self, query=False):
        return [term.lower() for term in re.findall(r'\w+', query or '') if len(term) >= 2]

    @api.model
    def _dashboard_query_score(self, article, terms):
        if not terms:
            return 0
        name = (article.name or '').lower()
        summary = (article.summary or '').lower()
        body = self._strip_html_to_text(article.body_html).lower()
        category = (article.category_id.complete_name or '').lower()
        tags = ' '.join(article.tag_ids.mapped('name')).lower()
        score = 0
        for term in terms:
            if term in name:
                score += 60
            if term in summary:
                score += 30
            if term in category:
                score += 25
            if term in tags:
                score += 25
            if term in body:
                score += 10
        return score

    @api.model
    def _dashboard_make_excerpt(self, article, terms, length=220):
        source = article.summary or self._strip_html_to_text(article.body_html) or ''
        if not source:
            return ''
        lowered = source.lower()
        first_match = -1
        for term in terms:
            position = lowered.find(term)
            if position >= 0 and (first_match < 0 or position < first_match):
                first_match = position
        if first_match >= 0:
            start = max(first_match - 70, 0)
        else:
            start = 0
        excerpt = source[start:start + length].strip()
        if start > 0:
            excerpt = '… ' + excerpt
        if start + length < len(source):
            excerpt += ' …'
        return excerpt

    @api.model
    def get_dashboard_article_action(self, category_id=False, query=False, state_filter=False, quick_filter=False, sort_by=False):
        """Return an act_window for the dashboard current selection.

        User-specific filters are built server-side because the Odoo 18 backend
        action context does not always expose frontend user services to custom
        OWL client actions.
        """
        domain = self._get_dashboard_domain(category_id, query, state_filter, quick_filter)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articoli Knowledge Base'),
            'res_model': 'company.knowledge.article',
            'views': [(False, 'list'), (False, 'kanban'), (False, 'form'), (False, 'pivot'), (False, 'graph')],
            'view_mode': 'list,kanban,form,pivot,graph',
            'domain': domain or [],
            'target': 'current',
            'context': {'dashboard_sort_by': sort_by or False},
        }

    @api.model
    def get_dashboard_sidebar_data(self, category_id=False, query=False, state_filter=False, quick_filter=False, sort_by=False, limit=40):
        """Return compact data used by the backend dashboard sidebar.

        The method deliberately uses normal ``search`` / ``read_group`` calls, not sudo,
        so Odoo ACLs and record rules continue to define what each user can see.
        """
        Category = self.env['company.knowledge.category']
        Article = self.env['company.knowledge.article']
        limit = min(int(limit or 40), 100)
        query = (query or '').strip()
        category_id = int(category_id or 0) or False
        state_filter = state_filter or False
        quick_filter = quick_filter or False
        sort_by = sort_by or ('relevance' if query else 'updated')
        terms = self._dashboard_query_terms(query)

        base_domain = [('active', '=', True)]
        if state_filter == 'review_pending':
            base_domain.append(('state', 'in', ['review', 'changes_requested']))
        elif state_filter == 'review_due':
            base_domain.append(('is_review_due', '=', True))
        elif state_filter:
            base_domain.append(('state', '=', state_filter))

        article_domain = self._get_dashboard_domain(category_id, query, state_filter, quick_filter)

        fetch_limit = max(limit, 250) if query or sort_by in ('relevance', 'recent') else limit
        articles = Article.search(article_domain, order=self._get_dashboard_order(sort_by, query), limit=fetch_limit)

        if sort_by == 'relevance' and terms:
            articles = articles.sorted(lambda article: (self._dashboard_query_score(article, terms), article.priority or '0', article.write_date or fields.Datetime.now()), reverse=True)
        elif sort_by == 'recent':
            my_logs = self.env['company.knowledge.view.log'].search([
                ('article_id', 'in', articles.ids),
                ('user_id', '=', self.env.user.id),
            ])
            recent_by_article = {log.article_id.id: log.last_viewed_on for log in my_logs}
            articles = articles.sorted(lambda article: recent_by_article.get(article.id) or article.write_date or fields.Datetime.now(), reverse=True)

        articles = articles[:limit]
        state_labels = dict(Article._fields['state'].selection)
        type_labels = dict(Article._fields['article_type'].selection)
        selected_category = Category.browse(category_id).exists() if category_id else Category.browse()

        visible_categories = Category.search([('active', '=', True)], order='sequence, complete_name')
        grouped = Article.read_group(
            base_domain + [('category_id', '!=', False)],
            ['category_id'],
            ['category_id'],
            lazy=False,
        )
        direct_count_by_category = {
            row['category_id'][0]: row.get('category_id_count', 0)
            for row in grouped
            if row.get('category_id')
        }
        child_map = {}
        for category in visible_categories:
            child_map.setdefault(category.parent_id.id or 0, []).append(category)

        flattened_categories = []

        def add_category_branch(category, level=0):
            total_count = direct_count_by_category.get(category.id, 0)
            for child in child_map.get(category.id, []):
                total_count += add_category_branch(child, level + 1)
            flattened_categories.append({
                'id': category.id,
                'name': category.name,
                'complete_name': category.complete_name,
                'parent_id': category.parent_id.id or False,
                'level': level,
                'direct_count': direct_count_by_category.get(category.id, 0),
                'article_count': total_count,
                'selected': category.id == category_id,
            })
            return total_count

        roots = child_map.get(0, [])
        for root in roots:
            add_category_branch(root, 0)
        flattened_categories.sort(key=lambda item: (item['complete_name'] or '').lower())

        my_logs = self.env['company.knowledge.view.log'].search([
            ('article_id', 'in', articles.ids),
            ('user_id', '=', self.env.user.id),
        ])
        my_last_viewed = {log.article_id.id: log.last_viewed_on for log in my_logs}

        def article_to_dict(article):
            matched_terms = []
            if terms:
                searchable = ' '.join([
                    article.name or '',
                    article.summary or '',
                    self._strip_html_to_text(article.body_html),
                    article.category_id.complete_name or '',
                    ' '.join(article.tag_ids.mapped('name')),
                ]).lower()
                matched_terms = [term for term in terms if term in searchable][:6]
            return {
                'id': article.id,
                'name': article.name,
                'summary': article.summary or '',
                'excerpt': self._dashboard_make_excerpt(article, terms),
                'category': article.category_id.complete_name or '',
                'area': article.area_id.name or '',
                'state': article.state,
                'state_label': state_labels.get(article.state, article.state),
                'article_type': article.article_type,
                'article_type_label': type_labels.get(article.article_type, article.article_type),
                'priority': article.priority,
                'view_count': article.view_count,
                'quality_score': article.quality_score,
                'quality_level': article.quality_level,
                'quality_issue_count': article.quality_issue_count,
                'is_favorite': bool(article.is_favorite),
                'is_subscribed_by_me': bool(article.is_subscribed_by_me),
                'requires_acknowledgement': bool(article.requires_acknowledgement),
                'is_acknowledged_by_me': bool(article.is_acknowledged_by_me),
                'review_date': fields.Date.to_string(article.review_date) if article.review_date else False,
                'write_date': fields.Datetime.to_string(article.write_date) if article.write_date else False,
                'last_viewed_by_me_on': fields.Datetime.to_string(my_last_viewed.get(article.id)) if my_last_viewed.get(article.id) else False,
                'tag_names': article.tag_ids.mapped('name')[:6],
                'matched_terms': matched_terms,
                'relevance_score': self._dashboard_query_score(article, terms),
                'attachment_count': article.attachment_count,
                'portal_visible': bool(article.portal_visible),
                'article_link_count': article.article_link_count,
                'feedback_todo_count': article.feedback_todo_count,
                'feedback_critical_count': article.feedback_critical_count,
            }

        counters = {
            'all': Article.search_count([('active', '=', True)]),
            'published': Article.search_count([('active', '=', True), ('state', '=', 'published')]),
            'draft': Article.search_count([('active', '=', True), ('state', '=', 'draft')]),
            'review': Article.search_count([('active', '=', True), ('state', 'in', ['review', 'changes_requested'])]),
            'review_due': Article.search_count([('active', '=', True), ('is_review_due', '=', True)]),
            'favorites': Article.search_count([('active', '=', True), ('favorite_ids.user_id', '=', self.env.user.id)]),
            'subscribed': Article.search_count([('active', '=', True), ('subscription_ids.user_id', '=', self.env.user.id), ('subscription_ids.active', '=', True)]),
            'ack_required': Article.search_count([('active', '=', True), ('requires_acknowledgement', '=', True), ('state', '=', 'published')]),
            'low_quality': Article.search_count([('active', '=', True), ('quality_score', '<', self._get_quality_min_score())]),
            'recent': Article.search_count([('active', '=', True), ('view_log_ids.user_id', '=', self.env.user.id)]),
            'with_attachments': Article.search_count([('active', '=', True), ('attachment_ids', '!=', False)]),
            'portal': Article.search_count([('active', '=', True), ('portal_visible', '=', True)]),
            'with_related': Article.search_count([('active', '=', True), ('related_article_link_ids', '!=', False)]),
            'feedback_todo': Article.search_count([('active', '=', True), ('feedback_ids.state', '=', 'todo')]),
            'feedback_critical': Article.search_count([
                ('active', '=', True),
                ('feedback_ids.state', '=', 'todo'),
                '|',
                ('feedback_ids.severity', 'in', ['high', 'critical']),
                ('feedback_ids.feedback_type', 'in', ['error', 'obsolete', 'missing']),
            ]),
        }

        return {
            'categories': flattened_categories,
            'articles': [article_to_dict(article) for article in articles],
            'counters': counters,
            'selected_category': {
                'id': selected_category.id,
                'name': selected_category.complete_name,
            } if selected_category else False,
            'state_filter': state_filter,
            'quick_filter': quick_filter,
            'sort_by': sort_by,
            'query': query,
            'limit': limit,
        }
