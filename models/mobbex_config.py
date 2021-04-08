# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
from datetime import datetime, timedelta, date
import requests
import json
import threading

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
	days_days_execution = fields.Integer('Cantidad de dias para intentar el debito', default=10)
	days_execute_after = fields.Integer('Dias para nuevo intento de debito')
	company_id = fields.Many2one('res.company', 'Empresa', required=False)
	journal_id = fields.Many2one('account.journal', 'Diario de Cobro', domain="[('type', 'in', ('cash', 'bank'))]")
	factura_electronica = fields.Boolean('Factura electronica')

	@api.one
	def button_mobbex_debit_execute(self):
		cr = self.env.cr
		uid = self.env.uid
		fecha_actual = date.today()
		_logger.info('Mobbex: iniciando debito de cuotas manual.')
		count = 0
		if len(self.company_id.mobbex_id) > 0:
			today = datetime.today()
			fecha_inicial = today.date().replace(day=1)
			cuotas_obj = self.pool.get('financiera.prestamo.cuota')
			cuotas_ids = cuotas_obj.search(cr, uid, [
				('company_id', '=', self.company_id.id),
				('prestamo_id.mobbex_debito_automatico', '=', True),
				('prestamo_id.mobbex_suscripcion_suscriptor_confirm', '=', True),
				('prestamo_id.state', '=', 'acreditado'),
				('state', '=', 'activa'),
				('fecha_vencimiento', '>=', fecha_inicial), 
				('fecha_vencimiento', '<=', fecha_actual),
			])
			create_on = datetime.now().replace(hour=4,minute=0,second=0,microsecond=0).strftime("%m/%d/%Y %H:%M:%S")
			for _id in cuotas_ids:
				cuota_id = cuotas_obj.browse(cr, uid, _id)
				execution_obj = self.pool.get('financiera.mobbex.execution')
				execution_ids = execution_obj.search(cr, uid, [
					('mobbex_cuota_id', '=', cuota_id.id),
					('create_date', '>=', create_on),
					('mobbex_status_code', '=', '410')
				])
				if not len(execution_ids) > 0:
					threading.Timer(count * TIME_BETWEEN_EXECUTION, cuota_id.mobbex_subscriber_execution()).start()
					count += 1
		_logger.info('Mobbex: finalizo el debito de cuotas manual: %s cuotas ejecutadas', count)
