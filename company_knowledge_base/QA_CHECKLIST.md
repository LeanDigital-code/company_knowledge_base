# QA Checklist for Marketplace Release

## Installation
- [ ] Install on a clean Odoo 18 Community database.
- [ ] Upgrade from previous stable release.
- [ ] Restart Odoo and rebuild assets.
- [ ] Verify no Python, XML, QWeb or JS errors in logs.

## Security
- [ ] Test Reader permissions.
- [ ] Test Editor permissions.
- [ ] Test Manager permissions.
- [ ] Test Administrator permissions.
- [ ] Verify group, user, area and portal visibility rules.
- [ ] Verify users cannot access restricted articles via direct URL.

## Functional Flows
- [ ] Create an article from scratch.
- [ ] Create an article from template.
- [ ] Submit for review.
- [ ] Request changes.
- [ ] Approve and publish.
- [ ] Create new revision.
- [ ] Compare versions.
- [ ] Restore a version.
- [ ] Add attachments.
- [ ] Add related articles.
- [ ] Follow/unfollow article.
- [ ] Mark article as read.
- [ ] Confirm required reading.
- [ ] Submit feedback.
- [ ] Resolve feedback.
- [ ] Send notifications.
- [ ] Import CSV.
- [ ] Export CSV.
- [ ] Export HTML.
- [ ] Export PDF.

## Dashboard
- [ ] Dashboard opens without OWL errors.
- [ ] Search works.
- [ ] Status filters work.
- [ ] Sorting works.
- [ ] Category navigation works.
- [ ] Article cards open the correct record.
- [ ] Responsive layout is acceptable.

## Portal
- [ ] Public knowledge page loads.
- [ ] Portal search works.
- [ ] Only portal-published articles are visible.
- [ ] Related portal articles are shown correctly.

## Commercial Assets
- [ ] Icon is visible.
- [ ] Banner is visible.
- [ ] Screenshots are readable.
- [ ] static/description/index.html renders correctly.
- [ ] README is complete.
- [ ] Changelog is included.
