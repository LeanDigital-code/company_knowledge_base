# -*- coding: utf-8 -*-
import base64
import csv
import io
import re
from html import unescape

from odoo import fields, models, _
from odoo.exceptions import UserError


def _html_to_text(value):
    value = value or ''
    value = re.sub(r'</(p|div|br|li|tr|h[1-6])\s*>', '\n', value, flags=re.IGNORECASE)
    value = re.sub(r'<[^>]+>', '', value)
    lines = [unescape(line).strip() for line in value.splitlines()]
    return '\n'.join(line for line in lines if line)


class CompanyKnowledgeExportWizard(models.TransientModel):
    _name = 'company.knowledge.export.wizard'
    _description = 'Esportazione articoli Knowledge Base'

    article_ids = fields.Many2many('company.knowledge.article', string='Articoli da esportare', required=True)
    export_format = fields.Selection(
        [('csv', 'CSV'), ('html', 'HTML leggibile'), ('pdf', 'PDF')],
        string='Formato',
        default='csv',
        required=True,
    )
    include_body_text = fields.Boolean(string='Includi testo contenuto', default=True)
    file_data = fields.Binary(string='File generato', readonly=True)
    file_name = fields.Char(string='Nome file', readonly=True)

    def _get_articles(self):
        self.ensure_one()
        articles = self.article_ids
        if not articles:
            raise UserError(_('Seleziona almeno un articolo da esportare.'))
        return articles

    def _generate_csv(self, articles):
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        headers = [
            'id', 'title', 'summary', 'article_type', 'category', 'area', 'tags', 'state', 'visibility',
            'owner', 'author', 'version', 'review_date', 'published_date', 'view_count', 'rating_avg'
        ]
        if self.include_body_text:
            headers.append('body_text')
        writer.writerow(headers)
        for article in articles:
            row = [
                article.id,
                article.name or '',
                article.summary or '',
                article.article_type or '',
                article.category_id.complete_name or '',
                article.area_id.name or '',
                ', '.join(article.tag_ids.mapped('name')),
                article.state or '',
                article.visibility or '',
                article.owner_id.display_name or '',
                article.author_id.display_name or '',
                article.version_number or 0,
                article.review_date or '',
                article.published_date or '',
                article.view_count or 0,
                article.rating_avg or 0.0,
            ]
            if self.include_body_text:
                row.append(_html_to_text(article.body_html) or '')
            writer.writerow(row)
        return output.getvalue().encode('utf-8-sig'), 'knowledge_articles.csv'

    def _generate_html(self, articles):
        parts = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>Knowledge Base Export</title></head><body>']
        parts.append('<h1>Knowledge Base Export</h1>')
        for article in articles:
            parts.append('<article style="page-break-after: always;">')
            parts.append('<h2>%s</h2>' % (article.name or ''))
            parts.append('<p><b>Categoria:</b> %s<br/><b>Area:</b> %s<br/><b>Stato:</b> %s<br/><b>Versione:</b> %s</p>' % (
                article.category_id.complete_name or '', article.area_id.name or '', article.state or '', article.version_number or 0))
            if article.summary:
                parts.append('<p><b>Descrizione:</b> %s</p>' % article.summary)
            parts.append(article.body_html or '')
            parts.append('</article>')
        parts.append('</body></html>')
        return '\n'.join(parts).encode('utf-8'), 'knowledge_articles.html'

    def action_generate_file(self):
        self.ensure_one()
        articles = self._get_articles()
        if self.export_format == 'pdf':
            return self.env.ref('company_knowledge_base.action_report_company_knowledge_article_pdf').report_action(articles)
        if self.export_format == 'csv':
            content, filename = self._generate_csv(articles)
        else:
            content, filename = self._generate_html(articles)
        self.write({
            'file_data': base64.b64encode(content),
            'file_name': filename,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Esporta articoli Knowledge Base'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_download_file(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError(_('Genera prima il file.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&id=%s&field=file_data&filename_field=file_name&download=true' % (self._name, self.id),
            'target': 'self',
        }
