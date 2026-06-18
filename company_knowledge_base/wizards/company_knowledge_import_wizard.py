# -*- coding: utf-8 -*-
import base64
import csv
import io

from odoo import fields, models, _
from odoo.exceptions import UserError


class CompanyKnowledgeImportWizard(models.TransientModel):
    _name = 'company.knowledge.import.wizard'
    _description = 'Importazione articoli Knowledge Base'

    file_data = fields.Binary(string='File CSV', required=True)
    file_name = fields.Char(string='Nome file')
    default_category_id = fields.Many2one('company.knowledge.category', string='Categoria predefinita', required=True)
    default_owner_id = fields.Many2one('res.users', string='Responsabile predefinito', default=lambda self: self.env.user)
    default_area_id = fields.Many2one('company.knowledge.area', string='Area/Reparto predefinito')
    create_missing_categories = fields.Boolean(string='Crea categorie mancanti', default=True)
    delimiter = fields.Selection(
        [('auto', 'Automatico'), (',', 'Virgola'), (';', 'Punto e virgola'), ('\t', 'Tabulazione')],
        string='Separatore',
        default='auto',
        required=True,
    )
    imported_count = fields.Integer(string='Articoli importati', readonly=True)
    skipped_count = fields.Integer(string='Righe saltate', readonly=True)
    result_html = fields.Html(string='Risultato', readonly=True)

    def _decode_csv(self):
        self.ensure_one()
        try:
            raw = base64.b64decode(self.file_data or b'')
        except Exception as exc:
            raise UserError(_('Impossibile leggere il file caricato: %s') % exc) from exc
        for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                text = False
        if not text:
            raise UserError(_('Formato del file non riconosciuto. Usa un CSV in UTF-8 o Latin-1.'))
        if self.delimiter == 'auto':
            sample = text[:2048]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ';' if ';' in sample else ','
        else:
            delimiter = self.delimiter
        return csv.DictReader(io.StringIO(text), delimiter=delimiter)

    def _normalize_key(self, row, *keys):
        lower_map = {(key or '').strip().lower(): value for key, value in row.items()}
        for key in keys:
            value = lower_map.get(key.lower())
            if value not in (None, ''):
                return str(value).strip()
        return False

    def _find_or_create_category(self, value):
        if not value:
            return self.default_category_id
        Category = self.env['company.knowledge.category'].sudo()
        category = Category.search(['|', ('complete_name', '=', value), ('name', '=', value)], limit=1)
        if category:
            return category
        if not self.create_missing_categories:
            return self.default_category_id
        parent = False
        name = value
        if '/' in value:
            pieces = [piece.strip() for piece in value.split('/') if piece.strip()]
            for piece in pieces:
                existing = Category.search([('name', '=', piece), ('parent_id', '=', parent.id if parent else False)], limit=1)
                parent = existing or Category.create({'name': piece, 'parent_id': parent.id if parent else False})
            return parent
        return Category.create({'name': name})

    def _find_tags(self, value):
        if not value:
            return []
        Tag = self.env['company.knowledge.tag'].sudo()
        tag_ids = []
        for tag_name in [tag.strip() for tag in value.replace('|', ',').split(',') if tag.strip()]:
            tag = Tag.search([('name', '=', tag_name)], limit=1) or Tag.create({'name': tag_name})
            tag_ids.append(tag.id)
        return tag_ids

    def _find_user(self, value):
        if not value:
            return self.default_owner_id
        User = self.env['res.users'].sudo()
        return User.search(['|', '|', ('login', '=', value), ('email', '=', value), ('name', '=', value)], limit=1) or self.default_owner_id

    def _find_area(self, value):
        if not value:
            return self.default_area_id
        Area = self.env['company.knowledge.area'].sudo()
        return Area.search(['|', ('name', '=', value), ('code', '=', value)], limit=1) or self.default_area_id

    def action_import(self):
        self.ensure_one()
        if not self.env.user.has_group('company_knowledge_base.group_company_knowledge_editor'):
            raise UserError(_('Solo Editor o Responsabili possono importare articoli.'))
        reader = self._decode_csv()
        if not reader.fieldnames:
            raise UserError(_('Il CSV non contiene intestazioni.'))
        Article = self.env['company.knowledge.article'].with_context(no_version_snapshot=False)
        imported = 0
        skipped = 0
        errors = []
        valid_types = dict(Article._fields['article_type'].selection)
        valid_visibility = dict(Article._fields['visibility'].selection)
        visibility_values = set(valid_visibility.keys())
        type_values = set(valid_types.keys())
        for line_number, row in enumerate(reader, start=2):
            title = self._normalize_key(row, 'title', 'titolo', 'name', 'nome')
            if not title:
                skipped += 1
                errors.append(_('Riga %s: titolo mancante.') % line_number)
                continue
            category = self._find_or_create_category(self._normalize_key(row, 'category', 'categoria'))
            owner = self._find_user(self._normalize_key(row, 'owner', 'responsabile', 'owner_login'))
            area = self._find_area(self._normalize_key(row, 'area', 'reparto', 'department'))
            article_type = self._normalize_key(row, 'article_type', 'tipo', 'type') or 'other'
            if article_type not in type_values:
                article_type = 'other'
            visibility = self._normalize_key(row, 'visibility', 'visibilita', 'visibilità') or 'internal'
            if visibility not in visibility_values:
                visibility = 'internal'
            vals = {
                'name': title,
                'summary': self._normalize_key(row, 'summary', 'descrizione', 'description') or False,
                'body_html': self._normalize_key(row, 'body_html', 'contenuto', 'content', 'body') or '',
                'category_id': category.id,
                'owner_id': owner.id if owner else False,
                'article_type': article_type,
                'visibility': visibility,
                'review_date': self._normalize_key(row, 'review_date', 'data_revisione') or False,
            }
            if area:
                vals['area_id'] = area.id
                if visibility == 'areas':
                    vals['allowed_area_ids'] = [(6, 0, [area.id])]
            tag_ids = self._find_tags(self._normalize_key(row, 'tags', 'tag'))
            if tag_ids:
                vals['tag_ids'] = [(6, 0, tag_ids)]
            try:
                Article.create(vals)
                imported += 1
            except Exception as exc:
                skipped += 1
                errors.append(_('Riga %s: %s') % (line_number, exc))
        result = '<p><b>%s</b>: %s</p><p><b>%s</b>: %s</p>' % (_('Articoli importati'), imported, _('Righe saltate'), skipped)
        if errors:
            result += '<ul>%s</ul>' % ''.join('<li>%s</li>' % err for err in errors[:50])
            if len(errors) > 50:
                result += '<p>%s</p>' % _('Mostrati solo i primi 50 errori.')
        self.write({'imported_count': imported, 'skipped_count': skipped, 'result_html': result})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Risultato importazione'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
