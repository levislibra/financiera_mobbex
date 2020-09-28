# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraMobbexConfig(models.Model):
	_name = 'financiera.mobbex.config'

	name = fields.Char('Nombre')
	company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env['res.company']._company_default_get('financiera.pagos.360.cuenta'))
	api_key = fields.Char('API Key')
	access_token = fields.Char('Token')
	return_url = fields.Char('Url posterior a la suscripcion')
	validate_id = fields.Boolean('Rechazar si el DNI no coincide contra la Tarjeta')
	accept_no_funds = fields.Boolean('Aceptar tarjeta que no posea fondos')
	company_id = fields.Many2one('res.company', 'Empresa', required=False)
	# available_balance = fields.Float("Saldo Disponible")
	# unavailable_balance = fields.Float("Saldo Pendiente")

	# journal_id = fields.Many2one('account.journal', 'Diario de Cobro', domain="[('type', 'in', ('cash', 'bank'))]")
	# factura_electronica = fields.Boolean('Factura electronica')

