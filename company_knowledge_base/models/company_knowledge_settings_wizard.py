# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CompanyKnowledgeSettingsWizard(models.TransientModel):
    _name = 'company.knowledge.settings.wizard'
    _description = 'Knowledge Base Settings'
    _rec_name = 'name'

    name = fields.Char(
        string='Titolo',
        default='Impostazioni Knowledge Base',
        readonly=True,
    )

    review_activity_enabled = fields.Boolean(
        string='Crea attività automatiche per revisioni in scadenza',
    )
    review_activity_days_before = fields.Integer(
        string='Giorni di anticipo attività revisione',
        help='Numero di giorni prima della data revisione in cui generare attività per il responsabile articolo.',
    )
    auto_notify_on_publish = fields.Boolean(
        string='Notifica automaticamente alla pubblicazione',
        help='Alla pubblicazione invia una comunicazione agli utenti che seguono l’articolo e al pubblico interno visibile.',
    )
    auto_notify_on_update = fields.Boolean(
        string='Notifica automaticamente gli aggiornamenti degli articoli pubblicati',
        help='Quando viene modificato un articolo già pubblicato invia una notifica agli utenti iscritti all’articolo.',
    )
    enforce_quality_on_review = fields.Boolean(
        string='Blocca revisione/pubblicazione se qualità insufficiente',
        help='Se attivo, il sistema impedisce invio in revisione e pubblicazione sotto la soglia configurata.',
    )
    quality_min_score = fields.Integer(
        string='Punteggio qualità minimo',
        help='Soglia minima da 0 a 100 usata dai controlli qualità contenuto.',
    )
    feedback_activity_enabled = fields.Boolean(
        string='Crea attività automatiche dai feedback critici',
        help='Quando un utente segnala errore, contenuto obsoleto, informazione mancante o non utile, crea un’attività per il responsabile articolo.',
    )
    feedback_activity_days = fields.Integer(
        string='Giorni scadenza attività feedback',
        help='Numero di giorni entro cui gestire un feedback critico o operativo.',
    )

    @api.model
    def _get_bool_param(self, key, default=False):
        value = self.env['ir.config_parameter'].sudo().get_param(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('1', 'true', 'yes', 'y', 'on')

    @api.model
    def _get_int_param(self, key, default=0):
        value = self.env['ir.config_parameter'].sudo().get_param(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        params = self.env['ir.config_parameter'].sudo()

        values = {
            'review_activity_enabled': self._get_bool_param('company_knowledge_base.review_activity_enabled', True),
            'review_activity_days_before': self._get_int_param('company_knowledge_base.review_activity_days_before', 7),
            'auto_notify_on_publish': self._get_bool_param('company_knowledge_base.auto_notify_on_publish', False),
            'auto_notify_on_update': self._get_bool_param('company_knowledge_base.auto_notify_on_update', False),
            'enforce_quality_on_review': self._get_bool_param('company_knowledge_base.enforce_quality_on_review', False),
            'quality_min_score': self._get_int_param('company_knowledge_base.quality_min_score', 70),
            'feedback_activity_enabled': self._get_bool_param('company_knowledge_base.feedback_activity_enabled', True),
            'feedback_activity_days': self._get_int_param('company_knowledge_base.feedback_activity_days', 3),
        }
        for field_name, value in values.items():
            if field_name in fields_list:
                res[field_name] = value
        return res

    @api.model
    def action_open_settings(self):
        wizard = self.create({'name': _('Impostazioni Knowledge Base')})
        view = self.env.ref('company_knowledge_base.view_company_knowledge_settings_wizard_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Impostazioni Knowledge Base'),
            'res_model': 'company.knowledge.settings.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_save(self):
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()

        params.set_param('company_knowledge_base.review_activity_enabled', bool(self.review_activity_enabled))
        params.set_param('company_knowledge_base.review_activity_days_before', int(self.review_activity_days_before or 0))
        params.set_param('company_knowledge_base.auto_notify_on_publish', bool(self.auto_notify_on_publish))
        params.set_param('company_knowledge_base.auto_notify_on_update', bool(self.auto_notify_on_update))
        params.set_param('company_knowledge_base.enforce_quality_on_review', bool(self.enforce_quality_on_review))
        params.set_param('company_knowledge_base.quality_min_score', int(self.quality_min_score or 0))
        params.set_param('company_knowledge_base.feedback_activity_enabled', bool(self.feedback_activity_enabled))
        params.set_param('company_knowledge_base.feedback_activity_days', int(self.feedback_activity_days or 0))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Impostazioni salvate'),
                'message': _('Le impostazioni Knowledge Base sono state aggiornate correttamente.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
