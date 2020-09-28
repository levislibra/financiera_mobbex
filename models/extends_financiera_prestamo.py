# -*- coding: utf-8 -*-

from openerp import models, fields, api

class ExtendsFinancieraPrestamo(models.Model):
	_inherit = 'financiera.prestamo' 
	_name = 'financiera.prestamo'

	mobbex_id = fields.Many2one('financiera.mobbex.config', related='company_id.mobbex_id')
	mobbex_debito_automatico = fields.Boolean('Mobbex - Debito automatico')
