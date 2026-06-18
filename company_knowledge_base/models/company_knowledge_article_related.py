# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyKnowledgeArticleRelated(models.Model):
    _name = 'company.knowledge.article.related'
    _description = 'Knowledge Base Related Odoo Record'
    _order = 'article_id, model_id, res_id'

    name = fields.Char(string='Nome collegamento', compute='_compute_name', store=True)
    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        ondelete='cascade',
        index=True,
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Modello Odoo',
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False)],
    )
    res_model = fields.Char(string='Nome tecnico modello', related='model_id.model', store=True, readonly=True)
    res_id = fields.Integer(string='ID record', required=True)
    record_display_name = fields.Char(string='Record', compute='_compute_record_display_name')
    note = fields.Char(string='Nota')

    _sql_constraints = [
        ('article_model_record_uniq', 'unique(article_id, model_id, res_id)', 'Questo record è già collegato all’articolo.'),
        ('res_id_positive', 'CHECK(res_id > 0)', 'L’ID record deve essere maggiore di zero.'),
    ]

    @api.depends('article_id.name', 'model_id.name', 'res_id')
    def _compute_name(self):
        for link in self:
            parts = []
            if link.article_id:
                parts.append(link.article_id.display_name)
            if link.model_id:
                parts.append(link.model_id.name or link.model_id.model)
            if link.res_id:
                parts.append(str(link.res_id))
            link.name = ' - '.join(parts) if parts else _('Collegamento')

    @api.depends('model_id', 'res_id')
    def _compute_record_display_name(self):
        for link in self:
            link.record_display_name = False
            if not link.model_id or not link.res_id:
                continue
            try:
                record = self.env[link.model_id.model].sudo().browse(link.res_id).exists()
                link.record_display_name = record.display_name if record else _('Record non trovato')
            except Exception:
                link.record_display_name = _('Record non disponibile')

    @api.constrains('model_id', 'res_id')
    def _check_related_record_exists(self):
        for link in self:
            if not link.model_id or not link.res_id:
                continue
            try:
                record = self.env[link.model_id.model].sudo().browse(link.res_id).exists()
            except Exception as error:
                raise ValidationError(_('Impossibile verificare il record collegato: %s') % error) from error
            if not record:
                raise ValidationError(_('Il record indicato non esiste nel modello selezionato.'))

    def action_open_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.record_display_name or self.display_name,
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }
