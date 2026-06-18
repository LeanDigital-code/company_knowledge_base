# -*- coding: utf-8 -*-
{
    'name': 'Knowledge Base Pro',
    'summary': 'Advanced knowledge base with workflow, versioning, portal, dashboard and quality checks',
    'description': """
Knowledge Base Pro for Odoo 18 Community
========================================

Advanced internal knowledge management module for Odoo 18 Community.

Centralize company procedures, policies, FAQs, technical guides and operational documentation directly inside Odoo.

Main features:
- Structured articles with categories, subcategories, tags and attachments
- Approval workflow for draft, review, approval, publication, obsolete and archived states
- User roles: Reader, Editor, Manager and Administrator
- Access rules by groups, users, departments/areas and portal visibility
- Automatic version history
- Version comparison and restore
- Article templates and quality rules
- Quality score with configurable minimum threshold
- Feedback, severity, resolution tracking and activities
- Favorites, subscriptions, reading history and reading acknowledgements
- Article notifications and notification logs
- Related articles and article suggestions
- Smart dashboard with sidebar navigation, search, filters and sorting
- Portal/public article publishing
- CSV import
- CSV, HTML and PDF export
- Article PDF report
- Dedicated Knowledge Base settings page

Compatible with Odoo 18 Community.
""",
    'version': '1.0',
    'category': 'Productivity/Knowledge',
    'author': 'Lean Digital Studio',
    'website': 'https://wwww,leandigitalstudio.it',
    'license': 'OPL-1',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/company_knowledge_security.xml',
        'security/ir.model.access.csv',
        'data/company_knowledge_data.xml',
        'data/company_knowledge_templates.xml',
        'data/company_knowledge_cron.xml',
        'reports/company_knowledge_article_report.xml',
        'views/company_knowledge_area_views.xml',
        'views/company_knowledge_category_views.xml',
        'views/company_knowledge_tag_views.xml',
        'views/company_knowledge_template_views.xml',
        'views/company_knowledge_article_related_views.xml',
        'views/company_knowledge_article_link_views.xml',
        'views/company_knowledge_workflow_log_views.xml',
        'views/company_knowledge_acknowledgement_views.xml',
        'views/company_knowledge_subscription_views.xml',
        'views/company_knowledge_favorite_views.xml',
        'views/company_knowledge_view_log_views.xml',
        'views/company_knowledge_notification_log_views.xml',
        'views/company_knowledge_article_version_views.xml',
        'views/company_knowledge_feedback_views.xml',
        'views/res_config_settings_views.xml',
        'wizards/company_knowledge_review_wizard_views.xml',
        'wizards/company_knowledge_version_compare_wizard_views.xml',
        'wizards/company_knowledge_import_wizard_views.xml',
        'wizards/company_knowledge_export_wizard_views.xml',
        'wizards/company_knowledge_notify_wizard_views.xml',
        'views/company_knowledge_article_views.xml',
        'views/company_knowledge_dashboard_views.xml',
        'views/company_knowledge_portal_templates.xml',
        'views/company_knowledge_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'company_knowledge_base/static/src/js/company_knowledge_dashboard.js',
            'company_knowledge_base/static/src/xml/company_knowledge_dashboard.xml',
            'company_knowledge_base/static/src/scss/company_knowledge_dashboard.scss',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'support': 'info@leandigitalstudio.it',
    'price': 39.99,
    'currency': 'EUR',
    'images': [
        'static/description/banner.png',
        'static/description/screenshot_dashboard.png',
        'static/description/screenshot_article.png',
        'static/description/screenshot_workflow.png',
        'static/description/screenshot_portal.png',
    ],
}
