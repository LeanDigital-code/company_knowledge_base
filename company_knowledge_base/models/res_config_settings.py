# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_knowledge_review_activity_enabled = fields.Boolean(
        string='Crea attività automatiche per revisioni in scadenza',
        config_parameter='company_knowledge_base.review_activity_enabled',
        default=True,
    )
    company_knowledge_review_activity_days_before = fields.Integer(
        string='Giorni di anticipo attività revisione',
        config_parameter='company_knowledge_base.review_activity_days_before',
        default=7,
        help='Numero di giorni prima della data revisione in cui generare attività per il responsabile articolo.',
    )

    company_knowledge_auto_notify_on_publish = fields.Boolean(
        string='Notifica automaticamente alla pubblicazione',
        config_parameter='company_knowledge_base.auto_notify_on_publish',
        default=False,
        help='Alla pubblicazione invia una comunicazione agli utenti che seguono l’articolo e al pubblico interno visibile.',
    )
    company_knowledge_auto_notify_on_update = fields.Boolean(
        string='Notifica automaticamente gli aggiornamenti degli articoli pubblicati',
        config_parameter='company_knowledge_base.auto_notify_on_update',
        default=False,
        help='Quando viene modificato un articolo già pubblicato invia una notifica agli utenti iscritti all’articolo.',
    )

    company_knowledge_enforce_quality_on_review = fields.Boolean(
        string='Blocca revisione/pubblicazione se qualità insufficiente',
        config_parameter='company_knowledge_base.enforce_quality_on_review',
        default=False,
        help='Se attivo, il sistema impedisce invio in revisione e pubblicazione sotto la soglia configurata.',
    )
    company_knowledge_quality_min_score = fields.Integer(
        string='Punteggio qualità minimo',
        config_parameter='company_knowledge_base.quality_min_score',
        default=70,
        help='Soglia minima da 0 a 100 usata dai controlli qualità contenuto.',
    )

    company_knowledge_feedback_activity_enabled = fields.Boolean(
        string='Crea attività automatiche dai feedback critici',
        config_parameter='company_knowledge_base.feedback_activity_enabled',
        default=True,
        help='Quando un utente segnala errore, contenuto obsoleto, informazione mancante o non utile, crea un’attività per il responsabile articolo.',
    )
    company_knowledge_feedback_activity_days = fields.Integer(
        string='Giorni scadenza attività feedback',
        config_parameter='company_knowledge_base.feedback_activity_days',
        default=3,
        help='Numero di giorni entro cui gestire un feedback critico o operativo.',
    )


    @api.model
    def action_company_knowledge_open_settings(self):
        """Open Knowledge Base settings as a dedicated module configuration page.

        The settings still use standard ir.config_parameter-backed fields, but
        the menu opens a real transient record directly. This avoids the generic
        technical list/form behavior with the misleading New button.
        """
        settings = self.create({})
        view = self.env.ref('company_knowledge_base.view_company_knowledge_res_config_settings_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Impostazioni Knowledge Base'),
            'res_model': 'res.config.settings',
            'res_id': settings.id,
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
                'module': 'company_knowledge_base',
            },
        }
