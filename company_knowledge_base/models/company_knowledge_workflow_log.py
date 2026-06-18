# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CompanyKnowledgeWorkflowLog(models.Model):
    _name = 'company.knowledge.workflow.log'
    _description = 'Knowledge Base Workflow Log'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Evento', compute='_compute_name', store=True)
    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    action = fields.Selection(
        selection=[
            ('create', 'Creazione'),
            ('submit_review', 'Invio in revisione'),
            ('request_changes', 'Richiesta modifiche'),
            ('approve', 'Approvazione'),
            ('publish', 'Pubblicazione'),
            ('new_revision', 'Nuova revisione'),
            ('obsolete', 'Marcato obsoleto'),
            ('archive', 'Archiviazione'),
            ('reset_draft', 'Ritorno in bozza'),
            ('restore_version', 'Ripristino versione'),
            ('portal_publish', 'Pubblicazione portale'),
            ('portal_unpublish', 'Rimozione portale'),
            ('other', 'Altro'),
        ],
        string='Azione',
        required=True,
        default='other',
    )
    from_state = fields.Selection(
        selection=[
            ('draft', 'Bozza'),
            ('review', 'In revisione'),
            ('changes_requested', 'Da modificare'),
            ('approved', 'Approvato'),
            ('published', 'Pubblicato'),
            ('obsolete', 'Obsoleto'),
            ('archived', 'Archiviato'),
        ],
        string='Da stato',
    )
    to_state = fields.Selection(
        selection=[
            ('draft', 'Bozza'),
            ('review', 'In revisione'),
            ('changes_requested', 'Da modificare'),
            ('approved', 'Approvato'),
            ('published', 'Pubblicato'),
            ('obsolete', 'Obsoleto'),
            ('archived', 'Archiviato'),
        ],
        string='A stato',
    )
    note = fields.Text(string='Nota / motivazione')
    user_id = fields.Many2one(
        'res.users',
        string='Utente',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
    )
    date = fields.Datetime(string='Data evento', default=fields.Datetime.now, required=True, readonly=True)

    @api.depends('article_id.name', 'action', 'date')
    def _compute_name(self):
        action_labels = dict(self._fields['action'].selection)
        for log in self:
            label = action_labels.get(log.action, _('Evento'))
            if log.article_id:
                log.name = '%s - %s' % (log.article_id.display_name, label)
            else:
                log.name = label
