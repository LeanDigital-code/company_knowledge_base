# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CompanyKnowledgeNotifyWizard(models.TransientModel):
    _name = 'company.knowledge.notify.wizard'
    _description = 'Notify Knowledge Article Users'

    article_id = fields.Many2one('company.knowledge.article', string='Articolo', required=True, readonly=True)
    notification_type = fields.Selection(
        selection=[
            ('publish', 'Pubblicazione'),
            ('update', 'Aggiornamento'),
            ('review', 'Revisione'),
            ('acknowledgement', 'Richiesta conferma lettura'),
            ('custom', 'Comunicazione manuale'),
        ],
        string='Tipo comunicazione',
        default='custom',
        required=True,
    )
    message = fields.Html(string='Messaggio', required=True)
    user_ids = fields.Many2many('res.users', 'company_knowledge_notify_user_rel', 'wizard_id', 'user_id', string='Utenti specifici')
    group_ids = fields.Many2many('res.groups', 'company_knowledge_notify_group_rel', 'wizard_id', 'group_id', string='Gruppi')
    area_ids = fields.Many2many('company.knowledge.area', 'company_knowledge_notify_area_rel', 'wizard_id', 'area_id', string='Aree / reparti')
    include_subscribers = fields.Boolean(string='Includi utenti che seguono l’articolo', default=True)
    include_author_owner = fields.Boolean(string='Includi autore e responsabile', default=True)
    require_acknowledgement = fields.Boolean(string='Richiedi conferma lettura')
    create_activity = fields.Boolean(string='Crea attività To-Do per i destinatari')
    activity_deadline = fields.Date(string='Scadenza attività')

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        article = self.env['company.knowledge.article'].browse(self.env.context.get('active_id'))
        if article:
            values['article_id'] = article.id
            if 'message' in fields_list:
                values['message'] = _('<p>È disponibile un aggiornamento per l’articolo <strong>%s</strong>.</p>') % article.display_name
            if 'user_ids' in fields_list and article.visibility == 'users':
                values['user_ids'] = [(6, 0, article.allowed_user_ids.ids)]
            if 'group_ids' in fields_list and article.visibility == 'groups':
                values['group_ids'] = [(6, 0, article.allowed_group_ids.ids)]
            if 'area_ids' in fields_list and article.visibility == 'areas':
                values['area_ids'] = [(6, 0, article.allowed_area_ids.ids)]
        return values

    def _collect_target_users(self):
        self.ensure_one()
        users = self.env['res.users']
        users |= self.user_ids
        for group in self.group_ids:
            users |= group.users
        for area in self.area_ids:
            users |= area.user_ids
        if self.include_subscribers:
            users |= self.env['company.knowledge.subscription'].sudo().search([('article_id', '=', self.article_id.id), ('active', '=', True)]).mapped('user_id')
        if self.include_author_owner:
            users |= self.article_id.author_id | self.article_id.owner_id
        users = users.filtered(lambda user: user.active and user.partner_id)
        # Avoid notifying public/share users without internal access to Odoo backend.
        users = users.filtered(lambda user: user.has_group('base.group_user'))
        return users

    def action_notify(self):
        self.ensure_one()
        self.article_id._check_manager_permission()
        users = self._collect_target_users()
        if not users:
            raise UserError(_('Nessun destinatario trovato. Seleziona almeno un utente, gruppo, area o iscritto.'))

        article = self.article_id
        if self.require_acknowledgement and not article.requires_acknowledgement:
            article.write({'requires_acknowledgement': True})

        partner_ids = users.mapped('partner_id').ids
        article.message_post(
            body=self.message,
            partner_ids=partner_ids,
            subtype_xmlid='mail.mt_comment',
        )

        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        log_values = []
        for user in users:
            activity = False
            if self.create_activity and activity_type:
                activity = self.env['mail.activity'].sudo().create({
                    'activity_type_id': activity_type.id,
                    'summary': _('Knowledge Base: %s') % article.display_name,
                    'note': self.message,
                    'res_model_id': self.env['ir.model']._get_id('company.knowledge.article'),
                    'res_id': article.id,
                    'user_id': user.id,
                    'date_deadline': self.activity_deadline or fields.Date.context_today(self),
                })
            log_values.append({
                'article_id': article.id,
                'user_id': user.id,
                'sent_by_id': self.env.user.id,
                'notification_type': self.notification_type,
                'message': self.message,
                'activity_created': bool(activity),
                'activity_id': activity.id if activity else False,
            })
        self.env['company.knowledge.notification.log'].sudo().create(log_values)
        self.env['company.knowledge.subscription'].sudo().search([('article_id', '=', article.id), ('user_id', 'in', users.ids), ('active', '=', True)]).write({'last_notified_on': fields.Datetime.now()})
        article.message_post(body=_('Comunicazione Knowledge Base inviata a %s destinatari.') % len(users))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Notifica inviata'),
                'message': _('Destinatari notificati: %s') % len(users),
                'type': 'success',
                'sticky': False,
            },
        }
