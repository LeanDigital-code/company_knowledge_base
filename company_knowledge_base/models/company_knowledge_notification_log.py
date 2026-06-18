# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CompanyKnowledgeNotificationLog(models.Model):
    _name = 'company.knowledge.notification.log'
    _description = 'Knowledge Notification Log'
    _order = 'sent_on desc, id desc'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Nome', compute='_compute_display_name', store=True)
    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    user_id = fields.Many2one('res.users', string='Destinatario', required=True, index=True)
    partner_id = fields.Many2one('res.partner', string='Partner', related='user_id.partner_id', store=True, readonly=True)
    sent_by_id = fields.Many2one('res.users', string='Inviata da', default=lambda self: self.env.user, readonly=True)
    sent_on = fields.Datetime(string='Data invio', default=fields.Datetime.now, readonly=True)
    notification_type = fields.Selection(
        selection=[
            ('publish', 'Pubblicazione'),
            ('update', 'Aggiornamento'),
            ('review', 'Revisione'),
            ('acknowledgement', 'Richiesta conferma lettura'),
            ('custom', 'Comunicazione manuale'),
        ],
        string='Tipo notifica',
        default='custom',
        required=True,
    )
    message = fields.Html(string='Messaggio')
    activity_created = fields.Boolean(string='Attività creata')
    activity_id = fields.Many2one('mail.activity', string='Attività collegata', readonly=True, ondelete='set null')

    @api.depends('article_id', 'user_id', 'notification_type')
    def _compute_display_name(self):
        type_labels = dict(self._fields['notification_type'].selection)
        for log in self:
            log.display_name = '%s - %s - %s' % (
                log.article_id.display_name or _('Articolo'),
                log.user_id.display_name or _('Utente'),
                type_labels.get(log.notification_type, log.notification_type),
            )

    def action_open_article(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.article_id.display_name,
            'res_model': 'company.knowledge.article',
            'view_mode': 'form',
            'res_id': self.article_id.id,
        }
