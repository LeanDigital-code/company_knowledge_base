# -*- coding: utf-8 -*-
from odoo import fields, http, _
from odoo.http import request
from werkzeug.exceptions import NotFound


class CompanyKnowledgePortalController(http.Controller):
    """Small public/portal-facing knowledge base.

    It intentionally uses sudo and a strict publication domain so external
    users can only see records that managers explicitly mark as portal-visible.
    """

    def _portal_domain(self):
        return [
            ('active', '=', True),
            ('state', '=', 'published'),
            ('visibility', '=', 'portal'),
        ]

    @http.route(['/company_knowledge', '/company_knowledge/page/<int:page>'], type='http', auth='public', website=False)
    def company_knowledge_index(self, page=1, search=None, category_id=None, **kwargs):
        Article = request.env['company.knowledge.article'].sudo()
        Category = request.env['company.knowledge.category'].sudo()
        domain = self._portal_domain()
        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('summary', 'ilike', search), ('body_html', 'ilike', search)]
        if category_id:
            try:
                domain.append(('category_id', '=', int(category_id)))
            except (TypeError, ValueError):
                pass
        articles = Article.search(domain, order='category_id, priority desc, name', limit=100)
        categories = Category.search([
            ('id', 'in', articles.mapped('category_id').ids),
        ], order='parent_path, sequence, name') if articles else Category.browse()
        return request.render('company_knowledge_base.company_knowledge_public_index', {
            'articles': articles,
            'categories': categories,
            'search': search or '',
            'category_id': int(category_id) if str(category_id or '').isdigit() else False,
        })

    @http.route('/company_knowledge/article/<int:article_id>', type='http', auth='public', website=False)
    def company_knowledge_article(self, article_id, **kwargs):
        article = request.env['company.knowledge.article'].sudo().search(
            self._portal_domain() + [('id', '=', article_id)],
            limit=1,
        )
        if not article:
            raise NotFound()
        now = fields.Datetime.now()
        article.sudo().write({
            'view_count': article.view_count + 1,
            'last_viewed_on': now,
        })
        related_links = article.related_article_link_ids.filtered(
            lambda link: link.active and link.related_article_id.portal_visible
        )
        return request.render('company_knowledge_base.company_knowledge_public_article', {
            'article': article,
            'related_links': related_links,
        })
