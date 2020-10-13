# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraMobbexConfig(models.Model):
	_name = 'financiera.mobbex.config'

	name = fields.Char('Nombre')
	api_key = fields.Char('API Key')
	access_token = fields.Char('Token')
	return_url = fields.Char('Url posterior a la suscripcion')
	validate_id = fields.Boolean('Rechazar si el DNI no coincide contra la Tarjeta')
	accept_no_funds = fields.Boolean('Aceptar tarjeta que no posea fondos')
	days_execute_on_expiration = fields.Integer('Primer dia a debitar con respecto al vencimiento')
	days_execute_after = fields.Integer('Dias para nuevo intento de debito')
	company_id = fields.Many2one('res.company', 'Empresa', required=False)
	journal_id = fields.Many2one('account.journal', 'Diario de Cobro', domain="[('type', 'in', ('cash', 'bank'))]")
	factura_electronica = fields.Boolean('Factura electronica')

