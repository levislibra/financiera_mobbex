# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)
URL_SUSCRIPTIONS = 'https://api.mobbex.com/p/subscriptions/'
TIME_BETWEEN_EXECUTION = 6
class FinancieraMobbexConfig(models.Model):
	_name = 'financiera.mobbex.config'

	name = fields.Char('Nombre')
	api_key = fields.Char('API Key')
	access_token = fields.Char('Token')
	set_default_payment = fields.Boolean('Marcar como medio de pago por defecto')
	return_url = fields.Char('Url posterior a la suscripcion')
	validate_id = fields.Boolean('Rechazar si el DNI no coincide contra la Tarjeta')
	accept_no_funds = fields.Boolean('Aceptar tarjeta que no posea fondos')
	days_execute_on_expiration = fields.Integer('Primer dia a debitar con respecto al vencimiento')
	company_id = fields.Many2one('res.company', 'Empresa', required=False)
	journal_id = fields.Many2one('account.journal', 'Diario de Cobro', domain="[('type', 'in', ('cash', 'bank'))]")
	factura_electronica = fields.Boolean('Factura electronica')
	config_execute_ids = fields.One2many('financiera.mobbex.config.execute', 'config_id', 'Ejecuciones')

	@api.one
	def update_nextcall(self):
		for execute_id in self.config_execute_ids:
			execute_id.update_nextcall()
