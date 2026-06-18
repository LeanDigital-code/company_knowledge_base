# Changelog

## 18.0.13.1.0 - Store Candidate Cleanup
- Shortened the commercial app name to Knowledge Base Pro.
- Rewritten manifest description in English.
- Added doc/index.rst.
- Cleaned README for marketplace usage.
- Added final Odoo Apps upload checklist.

## 18.0.13.0.7 - Settings Header Title Fix
- Fixed the technical breadcrumb/title shown on top of the Knowledge Base settings wizard.
- Added a proper record name so Odoo no longer displays `company.knowledge.settings.wizard,1`.
- The settings page now shows a cleaner and more user-friendly title.

## 18.0.13.0.6 - Module-owned Settings Wizard
- Replaced the previous res.config.settings UI with a dedicated module transient model.
- The settings page no longer appears as a generic Odoo general settings record.
- Knowledge Base settings now open from Knowledge Base > Configurazione > Impostazioni Knowledge Base.
- Values are still stored in ir.config_parameter for compatibility with existing logic.

## 18.0.13.0.5 - Dedicated Knowledge Base Settings
- Added a dedicated Knowledge Base settings page under Knowledge Base > Configurazione > Impostazioni Knowledge Base.
- Removed the confusing generic settings behavior with the visible New button.
- Improved settings layout using clearer sections for review, notifications, quality and feedback.
- Settings still use standard ir.config_parameter-backed Odoo configuration fields.

## 18.0.13.0.4 - Menu Grouping Patch
- Grouped the Knowledge Base top navigation into fewer sections.
- Added Dashboard submenu with operational and classic dashboards.
- Moved personal article views under Articoli > Personali.
- Moved review-related article views under Articoli > Workflow e revisione.
- Grouped all feedback views under Feedback.
- Moved Versions under Analisi.

## 18.0.13.0.3 - Safe Dashboard Recovery Patch
- Reverted to the last stable dashboard base.
- Fixed the white page regression caused by the previous dashboard patch.
- Fixed the Open list action using a local safe Odoo action.
- Improved sidebar filter readability with conservative CSS only.

## 18.0.13.0.0 - Commercial Candidate
- Prepared commercial packaging for Odoo Apps.
- Added marketplace description page.
- Added icon, banner and feature screenshots.
- Added proprietary license notice.
- Updated manifest metadata: price, currency, support, license and images.
- Added professional README and QA checklist.
- No functional feature changes from the stable v12.0.1 base.

## 18.0.12.0.1
- Improved dashboard sidebar filter button UI.

## 18.0.12.0.0
- Added enhanced feedback severity, deadlines, activities and dashboard indicators.
