# Knowledge Base Pro for Odoo 18 Community

Knowledge Base Pro is an advanced internal knowledge management module for Odoo 18 Community.

It helps companies centralize procedures, policies, FAQs, technical guides and operational documentation directly inside Odoo, with approval workflow, versioning, access rules, portal publishing, dashboard navigation, feedback management and quality checks.

## Key Features

- Structured knowledge articles
- Categories, subcategories and tags
- Configurable article templates
- Approval workflow
- Workflow history
- Version history
- Version comparison and restore
- Article quality score and quality rules
- Attachments
- User favorites
- Reading history
- Reading acknowledgements
- Article subscriptions
- Notifications and notification logs
- Feedback and issue management
- Critical feedback activities
- Department / area based visibility
- Group and user based visibility
- Portal/public article publishing
- Related articles
- CSV import
- CSV, HTML and PDF export
- Article PDF report
- Smart dashboard with sidebar navigation
- Advanced search, filters and sorting
- Dedicated Knowledge Base settings page

## User Roles

The module includes four role levels:

- Knowledge Base Reader
- Knowledge Base Editor
- Knowledge Base Manager
- Knowledge Base Administrator

Assign users to the correct security group from the Odoo user form.

## Installation

1. Copy the `company_knowledge_base` folder into your Odoo addons path.
2. Restart Odoo.
3. Update the Apps list.
4. Install `Knowledge Base Pro`.
5. Configure users, categories, templates and areas.

Command-line installation or update:

```bash
./odoo-bin -d YOUR_DATABASE -i company_knowledge_base
./odoo-bin -d YOUR_DATABASE -u company_knowledge_base
```

## Configuration

After installation, configure:

- Knowledge Base categories
- Article templates
- Departments / areas
- Security groups
- Quality rules
- Review reminder settings
- Notification settings
- Feedback activity settings

Open settings from:

```text
Knowledge Base > Configurazione > Impostazioni Knowledge Base
```

## Compatibility

- Odoo 18 Community
- Dependencies: `base`, `mail`, `web`

## License

OPL-1. See the `LICENSE` file.

## Support

For support, bug reports or customization requests, contact the vendor email configured in the module manifest.
