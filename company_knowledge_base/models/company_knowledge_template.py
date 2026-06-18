# -*- coding: utf-8 -*-
from odoo import fields, models, _


class CompanyKnowledgeTemplate(models.Model):
    _name = 'company.knowledge.template'
    _description = 'Knowledge Base Article Template'
    _order = 'sequence, name'

    name = fields.Char(string='Nome template', required=True, translate=True)
    sequence = fields.Integer(string='Sequenza', default=10)
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
        required=True,
        default='procedure',
    )
    category_id = fields.Many2one(
        'company.knowledge.category',
        string='Categoria predefinita',
        ondelete='set null',
    )
    tag_ids = fields.Many2many(
        'company.knowledge.tag',
        'company_knowledge_template_tag_rel',
        'template_id',
        'tag_id',
        string='Tag predefiniti',
    )
    summary = fields.Text(string='Sintesi predefinita', translate=True)
    body_html = fields.Html(string='Struttura contenuto', sanitize=True, translate=True)

    quality_check_enabled = fields.Boolean(
        string='Controllo qualità attivo',
        default=True,
        help='Abilita le regole di completezza contenuto per gli articoli creati con questo template.',
    )
    min_body_length = fields.Integer(
        string='Lunghezza minima contenuto',
        default=120,
        help='Numero minimo consigliato di caratteri testuali, esclusi i tag HTML.',
    )
    requires_summary = fields.Boolean(
        string='Sintesi obbligatoria',
        default=True,
    )
    requires_tags = fields.Boolean(
        string='Tag obbligatori',
        default=False,
    )
    requires_attachments = fields.Boolean(
        string='Allegati obbligatori',
        default=False,
    )
    required_section_keywords = fields.Text(
        string='Sezioni/parole chiave richieste',
        help='Inserisci una voce per riga, ad esempio: Scopo, Responsabili, Procedura, Controlli. '
             'Il controllo verifica che ogni voce sia presente nel contenuto dell’articolo.',
    )
    active = fields.Boolean(default=True)

    def action_create_article_from_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nuovo articolo da template'),
            'res_model': 'company.knowledge.article',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_template_id': self.id,
                'default_article_type': self.article_type,
                'default_category_id': self.category_id.id,
                'default_tag_ids': [(6, 0, self.tag_ids.ids)],
                'default_summary': self.summary,
                'default_body_html': self.body_html,
            },
        }
