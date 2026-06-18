# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CompanyKnowledgeFeedback(models.Model):
    _name = 'company.knowledge.feedback'
    _description = 'Knowledge Base Article Feedback'
    _inherit = ['mail.thread']
    _order = 'state, severity desc, due_date asc, create_date desc'

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
        readonly=True,
    )
    feedback_type = fields.Selection(
        selection=[
            ('useful', 'Utile'),
            ('not_useful', 'Non utile'),
            ('error', 'Errore'),
            ('obsolete', 'Contenuto obsoleto'),
            ('missing', 'Informazione mancante'),
            ('other', 'Altro'),
        ],
        string='Tipo feedback',
        default='useful',
        required=True,
        tracking=True,
    )
    severity = fields.Selection(
        selection=[
            ('low', 'Bassa'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('critical', 'Critica'),
        ],
        string='Severità',
        default='medium',
        required=True,
        tracking=True,
        help='Priorità operativa con cui gestire la segnalazione.',
    )
    rating = fields.Selection(
        selection=[
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
        ],
        string='Valutazione',
        tracking=True,
    )
    comment = fields.Text(string='Commento')
    state = fields.Selection(
        selection=[
            ('todo', 'Da gestire'),
            ('done', 'Risolto'),
            ('rejected', 'Scartato'),
        ],
        string='Stato',
        default='todo',
        required=True,
        tracking=True,
    )
    assigned_user_id = fields.Many2one(
        related='article_id.owner_id',
        string='Responsabile articolo',
        store=True,
        readonly=True,
    )
    due_date = fields.Date(
        string='Scadenza gestione',
        tracking=True,
        help='Data entro cui il feedback dovrebbe essere analizzato o risolto.',
    )
    activity_id = fields.Many2one(
        'mail.activity',
        string='Attività collegata',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    resolution_note = fields.Text(string='Nota risoluzione')
    resolved_by_id = fields.Many2one('res.users', string='Risolto/gestito da', readonly=True, copy=False)
    resolved_date = fields.Datetime(string='Data gestione', readonly=True, copy=False)
    active = fields.Boolean(default=True)

    @api.onchange('feedback_type')
    def _onchange_feedback_type(self):
        for feedback in self:
            if feedback.feedback_type in ('error', 'obsolete'):
                feedback.severity = 'critical'
            elif feedback.feedback_type in ('missing', 'not_useful'):
                feedback.severity = 'high'
            elif feedback.feedback_type == 'useful':
                feedback.severity = 'low'
            else:
                feedback.severity = feedback.severity or 'medium'

    @api.model_create_multi
    def create(self, vals_list):
        today = fields.Date.context_today(self)
        default_days = self._get_feedback_due_days()
        for vals in vals_list:
            feedback_type = vals.get('feedback_type') or 'useful'
            vals.setdefault('severity', self._default_severity_for_type(feedback_type))
            if not vals.get('due_date') and feedback_type in ('not_useful', 'error', 'obsolete', 'missing'):
                vals['due_date'] = fields.Date.add(today, days=default_days)
        records = super().create(vals_list)
        if self._feedback_activity_enabled() and not self.env.context.get('skip_feedback_activity'):
            actionable = records.filtered(lambda feedback: feedback._is_actionable_feedback())
            actionable._create_feedback_activities(check_permission=False)
        return records

    @api.model
    def _default_severity_for_type(self, feedback_type):
        if feedback_type in ('error', 'obsolete'):
            return 'critical'
        if feedback_type in ('missing', 'not_useful'):
            return 'high'
        if feedback_type == 'useful':
            return 'low'
        return 'medium'

    @api.model
    def _feedback_activity_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'company_knowledge_base.feedback_activity_enabled', 'True'
        )
        return str(value).lower() not in ('0', 'false', 'no')

    @api.model
    def _get_feedback_due_days(self):
        try:
            return max(int(self.env['ir.config_parameter'].sudo().get_param(
                'company_knowledge_base.feedback_activity_days', '3'
            ) or 3), 0)
        except ValueError:
            return 3

    def _is_actionable_feedback(self):
        self.ensure_one()
        return self.state == 'todo' and self.feedback_type in ('not_useful', 'error', 'obsolete', 'missing')

    def _check_manage_permission(self):
        if not (
            self.env.user.has_group('company_knowledge_base.group_company_knowledge_editor')
            or self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager')
        ):
            raise UserError(_('Solo Editor o Responsabili possono gestire i feedback.'))

    def action_open_article(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.article_id.display_name,
            'res_model': 'company.knowledge.article',
            'res_id': self.article_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_feedback_activities(self, check_permission=True):
        if check_permission:
            self._check_manage_permission()
        created = 0
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_type:
            raise UserError(_('Tipo attività To-Do non trovato.'))
        for feedback in self:
            if not feedback._is_actionable_feedback():
                continue
            if feedback.activity_id and feedback.activity_id.exists():
                continue
            article = feedback.article_id
            responsible = feedback.assigned_user_id or article.owner_id or article.author_id or self.env.user
            deadline = feedback.due_date or fields.Date.add(fields.Date.context_today(self), days=self._get_feedback_due_days())
            article_for_activity = article.sudo() if not check_permission else article
            activity = article_for_activity.activity_schedule(
                activity_type_id=todo_type.id,
                summary=_('Gestire feedback Knowledge Base'),
                note=_(
                    '<p><strong>Tipo:</strong> %(type)s</p>'
                    '<p><strong>Severità:</strong> %(severity)s</p>'
                    '<p><strong>Commento:</strong><br/>%(comment)s</p>'
                ) % {
                    'type': dict(self._fields['feedback_type'].selection).get(feedback.feedback_type, feedback.feedback_type),
                    'severity': dict(self._fields['severity'].selection).get(feedback.severity, feedback.severity),
                    'comment': feedback.comment or _('Nessun commento inserito.'),
                },
                user_id=responsible.id,
                date_deadline=deadline,
            )
            target_feedback = feedback.sudo() if not check_permission else feedback
            target_feedback.write({'activity_id': getattr(activity, 'id', False) if activity else False, 'due_date': deadline})
            created += 1
        return created

    def action_create_activity(self):
        created = self._create_feedback_activities(check_permission=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Attività feedback'),
                'message': _('Attività create: %s') % created,
                'type': 'success',
                'sticky': False,
            },
        }

    def _close_linked_activity(self, note=False):
        for feedback in self:
            if feedback.activity_id and feedback.activity_id.exists():
                try:
                    feedback.activity_id.action_done(feedback=note or feedback.resolution_note or '')
                except Exception:
                    feedback.activity_id.unlink()

    def action_mark_done(self):
        self._check_manage_permission()
        now = fields.Datetime.now()
        for feedback in self:
            feedback.write({
                'state': 'done',
                'resolved_by_id': self.env.user.id,
                'resolved_date': now,
            })
        self._close_linked_activity(_('Feedback risolto dalla Knowledge Base.'))
        return True

    def action_reject(self):
        self._check_manage_permission()
        now = fields.Datetime.now()
        for feedback in self:
            feedback.write({
                'state': 'rejected',
                'resolved_by_id': self.env.user.id,
                'resolved_date': now,
            })
        self._close_linked_activity(_('Feedback scartato dalla Knowledge Base.'))
        return True

    def action_reset_todo(self):
        self._check_manage_permission()
        self.write({
            'state': 'todo',
            'resolved_by_id': False,
            'resolved_date': False,
        })
        return True
