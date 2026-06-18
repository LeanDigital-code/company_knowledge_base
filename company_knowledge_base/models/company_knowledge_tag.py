# -*- coding: utf-8 -*-
from odoo import fields, models


class CompanyKnowledgeTag(models.Model):
    _name = 'company.knowledge.tag'
    _description = 'Knowledge Base Tag'
    _order = 'name'

    name = fields.Char(string='Nome', required=True, translate=True)
    color = fields.Integer(string='Colore')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Esiste già un tag con questo nome.'),
    ]
