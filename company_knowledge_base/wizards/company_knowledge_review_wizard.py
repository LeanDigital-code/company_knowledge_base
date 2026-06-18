# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class CompanyKnowledgeReviewWizard(models.TransientModel):
    _name = 'company.knowledge.review.wizard'
    _description = 'Knowledge Base Review Wizard'

    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        readonly=True,
    )
    action_type = fields.Selection(
        selection=[
            ('request_changes', 'Richiedi modifiche'),
        ],
        string='Azione',
        default='request_changes',
        required=True,
        readonly=True,
    )
    note = fields.Text(string='Motivazione', required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.action_type != 'request_changes':
            raise UserError(_('Azione non supportata.'))
        self.article_id.action_request_changes(note=self.note)
        return {'type': 'ir.actions.act_window_close'}
