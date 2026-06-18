# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CompanyKnowledgeSubscription(models.Model):
    _name = 'company.knowledge.subscription'
    _description = 'Knowledge Article Subscription'
    _order = 'subscribed_on desc, id desc'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Nome', compute='_compute_display_name', store=True)
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
        required=True,
        default=lambda self: self.env.user,
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        related='user_id.partner_id',
        store=True,
        readonly=True,
    )
    notification_level = fields.Selection(
        selection=[
            ('major', 'Solo pubblicazioni e revisioni importanti'),
            ('all', 'Tutti gli aggiornamenti'),
        ],
        string='Livello notifiche',
        default='major',
        required=True,
    )
    subscribed_on = fields.Datetime(string='Data iscrizione', default=fields.Datetime.now, readonly=True)
    last_notified_on = fields.Datetime(string='Ultima notifica', readonly=True)
    active = fields.Boolean(default=True)
    note = fields.Text(string='Note')

    _sql_constraints = [
        ('article_user_unique', 'unique(article_id, user_id)', 'L’utente segue già questo articolo.'),
    ]

    @api.depends('article_id', 'user_id')
    def _compute_display_name(self):
        for subscription in self:
            article = subscription.article_id.display_name or _('Articolo')
            user = subscription.user_id.display_name or _('Utente')
            subscription.display_name = '%s - %s' % (article, user)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.user_id.partner_id and record.user_id.partner_id not in record.article_id.message_partner_ids:
                record.article_id.sudo().message_subscribe(partner_ids=[record.user_id.partner_id.id])
        return records

    def action_unsubscribe(self):
        for subscription in self:
            if subscription.user_id != self.env.user and not self.env.user.has_group('company_knowledge_base.group_company_knowledge_manager'):
                raise UserError(_('Puoi annullare solo le tue iscrizioni.'))
            subscription.unlink()
        return True

    def action_open_article(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.article_id.display_name,
            'res_model': 'company.knowledge.article',
            'view_mode': 'form',
            'res_id': self.article_id.id,
        }
