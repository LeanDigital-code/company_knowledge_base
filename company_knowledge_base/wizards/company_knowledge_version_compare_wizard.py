# -*- coding: utf-8 -*-
import difflib
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_TAG_RE = re.compile(r'<[^>]+>')


def _html_to_text(value):
    """Return a readable plain-text representation of an HTML field."""
    value = value or ''
    value = re.sub(r'</(p|div|br|li|tr|h[1-6])\s*>', '\n', value, flags=re.IGNORECASE)
    value = _TAG_RE.sub('', value)
    value = value.replace('&nbsp;', ' ')
    value = value.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    lines = [line.strip() for line in value.splitlines()]
    return '\n'.join(line for line in lines if line)


class CompanyKnowledgeVersionCompareWizard(models.TransientModel):
    _name = 'company.knowledge.version.compare.wizard'
    _description = 'Confronto versioni Knowledge Base'

    article_id = fields.Many2one(
        'company.knowledge.article',
        string='Articolo',
        required=True,
        readonly=True,
    )
    left_version_id = fields.Many2one(
        'company.knowledge.article.version',
        string='Versione precedente',
        required=True,
        domain="[('article_id', '=', article_id)]",
    )
    right_version_id = fields.Many2one(
        'company.knowledge.article.version',
        string='Versione successiva',
        required=True,
        domain="[('article_id', '=', article_id)]",
    )
    compare_scope = fields.Selection(
        selection=[
            ('body', 'Solo contenuto'),
            ('summary_body', 'Descrizione + contenuto'),
            ('metadata_summary_body', 'Metadati + descrizione + contenuto'),
        ],
        string='Ambito confronto',
        default='summary_body',
        required=True,
    )
    diff_html = fields.Html(string='Differenze', readonly=True, sanitize=False)
    diff_generated = fields.Boolean(string='Confronto generato', readonly=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        article_id = self.env.context.get('default_article_id') or self.env.context.get('active_id')
        if self.env.context.get('active_model') == 'company.knowledge.article.version':
            version = self.env['company.knowledge.article.version'].browse(self.env.context.get('active_id')).exists()
            if version:
                article_id = version.article_id.id
                values.setdefault('left_version_id', version.id)
        if article_id:
            article = self.env['company.knowledge.article'].browse(article_id).exists()
            if article:
                values['article_id'] = article.id
                versions = article.version_ids.sorted(lambda version: (version.create_date or fields.Datetime.now(), version.id), reverse=True)
                if len(versions) >= 2:
                    values.setdefault('right_version_id', versions[0].id)
                    values.setdefault('left_version_id', versions[1].id)
                elif len(versions) == 1:
                    values.setdefault('left_version_id', versions[0].id)
                    values.setdefault('right_version_id', versions[0].id)
        return values

    @api.constrains('article_id', 'left_version_id', 'right_version_id')
    def _check_versions(self):
        for wizard in self:
            if wizard.left_version_id.article_id != wizard.article_id or wizard.right_version_id.article_id != wizard.article_id:
                raise ValidationError(_('Le versioni selezionate devono appartenere allo stesso articolo.'))

    def _version_to_lines(self, version):
        self.ensure_one()
        sections = []
        if self.compare_scope == 'metadata_summary_body':
            sections.extend([
                _('Titolo: %s') % (version.title or ''),
                _('Tipo: %s') % (dict(version._fields['article_type'].selection).get(version.article_type, version.article_type or '') or ''),
                _('Categoria: %s') % (version.category_id.display_name or ''),
                _('Area/Reparto: %s') % (version.area_id.display_name or ''),
                _('Tag: %s') % ', '.join(version.tag_ids.mapped('display_name')),
                _('Stato snapshot: %s') % (dict(version._fields['snapshot_state_value'].selection).get(version.snapshot_state_value, version.snapshot_state_value or '') or ''),
                _('Data revisione: %s') % (version.review_date or ''),
                _('Richiede conferma lettura: %s') % (_('Sì') if version.requires_acknowledgement else _('No')),
                '',
            ])
        if self.compare_scope in ('summary_body', 'metadata_summary_body'):
            sections.extend([
                _('--- Descrizione breve ---'),
                version.summary or '',
                '',
            ])
        sections.extend([
            _('--- Contenuto ---'),
            _html_to_text(version.body_html),
        ])
        return '\n'.join(sections).splitlines()

    def action_compare(self):
        self.ensure_one()
        if not self.left_version_id or not self.right_version_id:
            raise UserError(_('Seleziona due versioni da confrontare.'))
        left_label = self.left_version_id.display_name
        right_label = self.right_version_id.display_name
        differ = difflib.HtmlDiff(wrapcolumn=100)
        diff_table = differ.make_table(
            self._version_to_lines(self.left_version_id),
            self._version_to_lines(self.right_version_id),
            fromdesc=left_label,
            todesc=right_label,
            context=True,
            numlines=5,
        )
        self.write({
            'diff_html': '<div class="o_company_knowledge_diff">%s</div>' % diff_table,
            'diff_generated': True,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confronta versioni'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_restore_left_version(self):
        self.ensure_one()
        return self.left_version_id.action_restore_version()

    def action_restore_right_version(self):
        self.ensure_one()
        return self.right_version_id.action_restore_version()
