# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools
from datetime import datetime, timedelta, date
from dateutil import relativedelta
import logging

import requests
import json
import threading

_logger = logging.getLogger(__name__)
URL_SUSCRIPTIONS = 'https://api.mobbex.com/p/subscriptions/'
TIME_BETWEEN_EXECUTION = 6.0

class ExtendsFinancieraPrestamoCuota(models.Model):
	_inherit = 'financiera.prestamo.cuota' 
	_name = 'financiera.prestamo.cuota'

	mobbex_id = fields.Many2one('financiera.mobbex.config', related='company_id.mobbex_id', readonly=True)
	mobbex_ejecucion_ids = fields.One2many('financiera.mobbex.execution', 'mobbex_cuota_id', 'Ejecuciones')
	mobbex_program_execution_date = fields.Date('Fecha de ejecucion programada')
	# Datos del prestamo
	mobbex_suscriptor_id = fields.Char(related='prestamo_id.mobbex_suscriptor_id')
	mobbex_suscriptor_sourceUrl = fields.Char(related='prestamo_id.mobbex_suscriptor_sourceUrl')
	mobbex_suscriptor_subscriberUrl = fields.Char(related='prestamo_id.mobbex_suscriptor_subscriberUrl')
	mobbex_suscripcion_suscriptor_confirm = fields.Boolean(related='prestamo_id.mobbex_suscripcion_suscriptor_confirm')
	mobbex_stop_debit = fields.Boolean('Stop debit')

	# @api.model
	# def _mobbex_debit_execute(self):
	# 	cr = self.env.cr
	# 	uid = self.env.uid
	# 	fecha_actual = date.today()
	# 	company_obj = self.pool.get('res.company')
	# 	comapny_ids = company_obj.search(cr, uid, [])
	# 	_logger.info('Mobbex: iniciando debito de cuotas.')
	# 	count = 0
	# 	for _id in comapny_ids:
	# 		company_id = company_obj.browse(cr, uid, _id)
	# 		if len(company_id.mobbex_id) > 0:
	# 			mobbex_id = company_id.mobbex_id
	# 			primer_fecha = fecha_actual - relativedelta.relativedelta(days=mobbex_id.days_execute_on_expiration)
	# 			cuotas_obj = self.pool.get('financiera.prestamo.cuota')
	# 			cuotas_ids = cuotas_obj.search(cr, uid, [
	# 				('company_id', '=', company_id.id),
	# 				('prestamo_id.mobbex_debito_automatico', '=', True),
	# 				('prestamo_id.mobbex_suscripcion_suscriptor_confirm', '=', True),
	# 				('prestamo_id.state', '=', 'acreditado'),
	# 				('state', '=', 'activa'),
	# 				('mobbex_stop_debit', '=', False),
	# 				'|', ('fecha_vencimiento', '<=', primer_fecha.__str__()), 
	# 				('fecha_vencimiento', '<=', fecha_actual),
	# 			])
	# 			partner_execute_ids = []
	# 			create_on = datetime.now().replace(hour=4,minute=0,second=0,microsecond=0).strftime("%m/%d/%Y %H:%M:%S")
	# 			today = date.today()
	# 			for _id in cuotas_ids:
	# 				cuota_id = cuotas_obj.browse(cr, uid, _id)
	# 				if cuota_id.partner_id.id not in partner_execute_ids:
	# 					execution_obj = self.pool.get('financiera.mobbex.execution')
	# 					execution_ids = []
	# 					if len(execution_ids) == 0:
	# 						# threading.Timer((count+1) * TIME_BETWEEN_EXECUTION, cuota_id.mobbex_subscriber_execution).start()
	# 						cuota_id.mobbex_subscriber_execution()
	# 						partner_execute_ids.append(cuota_id.partner_id.id)
	# 						count += 1
	# 	_logger.info('Mobbex: finalizo el debito de cuotas: %s cuotas ejecutadas', count)

	@api.model
	def _mobbex_debit_execute_company(self, arg_id, arg_amount=None):
		cr = self.env.cr
		uid = self.env.uid
		fecha_actual = date.today()
		_logger.info('Mobbex: iniciando debito de cuotas de la Empresa %s', arg_id)
		count = 0
		company_obj = self.pool.get('res.company')
		company_id = company_obj.browse(cr, uid, arg_id)
		if len(company_id.mobbex_id) > 0:
			mobbex_id = company_id.mobbex_id
			primer_fecha = fecha_actual - relativedelta.relativedelta(days=mobbex_id.days_execute_on_expiration)
			cuotas_obj = self.pool.get('financiera.prestamo.cuota')
			cuotas_ids = cuotas_obj.search(cr, uid, [
				('company_id', '=', company_id.id),
				('prestamo_id.mobbex_debito_automatico', '=', True),
				('prestamo_id.mobbex_stop_automatico', '=', False),
				('prestamo_id.mobbex_suscripcion_suscriptor_confirm', '=', True),
				('prestamo_id.state', '=', 'acreditado'),
				('state', '=', 'activa'),
				('mobbex_stop_debit', '=', False),
				'|', ('fecha_vencimiento', '<=', primer_fecha.__str__()), 
				('fecha_vencimiento', '<=', fecha_actual),
			])
			partner_execute_ids = []
			for _id in cuotas_ids:
				cuota_id = cuotas_obj.browse(cr, uid, _id)
				if cuota_id.partner_id.id not in partner_execute_ids:
					amount = None
					if arg_amount:
						amount = min(amount, float(arg_amount))
					cuota_id.mobbex_subscriber_execution(amount)
					partner_execute_ids.append(cuota_id.partner_id.id)
					count += 1
		_logger.info('Mobbex: finalizo el debito de cuotas: %s cuotas ejecutadas', count)

	@api.multi
	def mobbex_subscriber_execution(self, monto=None):
		with api.Environment.manage():
			# As this function is in a new thread, I need to open a new cursor, because the old one may be closed
			new_cr = self.pool.cursor()
			self = self.with_env(self.env(cr=new_cr))
			# scheduler_cron = self.sudo().env.ref('procurement.ir_cron_scheduler_action')
			if self.prestamo_id and self.prestamo_id.mobbex_suscripcion_id and self.prestamo_id.mobbex_suscriptor_id:
				url = URL_SUSCRIPTIONS+self.prestamo_id.mobbex_suscripcion_id
				url += '/subscriber/'+self.prestamo_id.mobbex_suscriptor_id
				url += '/execution/'
				headers = {
					'x-api-key': self.mobbex_id.api_key,
					'x-access-token': self.mobbex_id.access_token,
					'content-type': 'application/json',
				}
				total = self.saldo
				if monto:
					total = min(monto, self.saldo)
				reference = str(self.id) + '_' + str(len(self.payment_ids))
				body = {
					'total': total,
					'reference': reference,
				}
				r = requests.post(url, data=json.dumps(body), headers=headers)
				data = r.json()
				if 'result' in data and data['result'] == True:
					pass
			new_cr.close()

	@api.one
	def mobbex_read_execution(self, data):
		if self.state in ('activa','judicial','incobrable') and self.saldo > 0:
			values = {
				'company_id': self.company_id.id,
				# 'mobbex_cuota_id': self.id,
			}
			if 'payment' in data and 'status' in data['payment'] and 'code' in data['payment']['status']:
				values['mobbex_status_code'] = data['payment']['status']['code']
			if 'payment' in data and 'status' in data['payment'] and 'text' in data['payment']['status']:
				values['mobbex_status_text'] = data['payment']['status']['text']
			if 'payment' in data and 'status' in data['payment'] and 'message' in data['payment']['status']:
				values['mobbex_status_message'] = data['payment']['status']['message']
			if 'payment' in data and 'total' in data['payment']:
				values['mobbex_total'] = data['payment']['total']
			if 'payment' in data and 'created' in data['payment']:
				values['mobbex_created'] = data['payment']['created']
			if 'payment' in data and 'currency' in data['payment'] and 'code' in data['payment']['currency']:
				values['mobbex_currency_code'] = data['payment']['currency']['code']
			if 'payment' in data and 'currency' in data['payment'] and 'text' in data['payment']['currency']:
				values['mobbex_currency_text'] = data['payment']['currency']['text']
			if 'payment' in data and 'source' in data['payment'] and 'name' in data['payment']['source']:
				values['mobbex_source_name'] = data['payment']['source']['name']
			if 'payment' in data and 'source' in data['payment'] and 'type' in data['payment']['source']:
				values['mobbex_source_type'] = data['payment']['source']['type']
			if 'payment' in data and 'source' in data['payment'] and 'number' in data['payment']['source']:
				values['mobbex_source_number'] = data['payment']['source']['number']
			if 'execution' in data and 'uid' in data['execution']:
				values['mobbex_ejecucion_id'] = data['execution']['uid']
			if 'payment' in data and 'id' in data['payment']:
				values['mobbex_operation_id'] = data['payment']['id']
			execution_id = self.env['financiera.mobbex.execution'].create(values)
			self.mobbex_ejecucion_ids = [execution_id.id]
			if execution_id.mobbex_status_code == '200':
				self.mobbex_cobrar_cuota(execution_id)
				# si saldo es menor a un peso (por problemas de redondeo)
				if self.saldo > 1:
					self.mobbex_subscriber_execution()
				if self.cuota_proxima_id and not self.cuota_proxima_id.mobbex_stop_debit and self.cuota_proxima_id.saldo > 0 and self.cuota_proxima_id.state_mora in ['moraTemprana', 'moraMedia', 'moraTardia', 'incobrable']:
					self.cuota_proxima_id.mobbex_subscriber_execution()
			elif execution_id.mobbex_status_code in ['400','411','413','417']:
				self.prestamo_id.mobbex_stop_automatico = True
				self.prestamo_id.mobbex_stop_motivo = execution_id.mobbex_status_message
				self.prestamo_id.mobbex_stop_cantidad = self.prestamo_id.mobbex_stop_cantidad + 1
			elif execution_id.mobbex_status_code in ['414', '415','416']:
				self.prestamo_id.mobbex_stop_cantidad = self.prestamo_id.mobbex_stop_cantidad + 1
				if self.prestamo_id.mobbex_stop_cantidad > 9:
					self.prestamo_id.mobbex_stop_automatico = True
					self.prestamo_id.mobbex_stop_motivo = execution_id.mobbex_status_message
				
			
	@api.one
	def mobbex_read_execution_aprobado(self, data):
		if self.state in ('activa','judicial','incobrable') and self.saldo > 0:
			values = {
				'company_id': self.company_id.id,
				# 'mobbex_cuota_id': self.id,
			}
			values['mobbex_status_code'] = data['status']
			values['mobbex_status_text'] = 'Aprobado'
			values['mobbex_status_message'] = 'Transacción Aprobada'
			values['mobbex_total'] = data['total']
			values['mobbex_created'] = data['created']
			values['mobbex_currency_code'] = data['currency']
			values['mobbex_currency_text'] = data['totals']['currency_data']['label']
			values['mobbex_source_name'] = data['sourceName']
			values['mobbex_source_type'] = 'card'
			values['mobbex_source_number'] = data['card_number']
			# values['mobbex_ejecucion_id'] = 
			# values['mobbex_operation_id'] = 
			execution_id = self.env['financiera.mobbex.execution'].create(values)
			self.mobbex_ejecucion_ids = [execution_id.id]
			if execution_id.mobbex_status_code == '200':
				self.mobbex_cobrar_cuota(execution_id)

	@api.one
	def mobbex_cobrar_cuota(self, execution_id=None):
		# Cobro cuota
		# cr = self.env.cr
		# uid = self.env.uid
		# superuser_id = self.pool.get('res.users').browse(cr, uid, 1)
		# superuser_id.company_id = self.company_id.id
		payment_date = datetime.now()
		journal_id = self.mobbex_id.journal_id
		factura_electronica = self.mobbex_id.factura_electronica
		partner_id = self.partner_id
		amount = self.saldo
		if execution_id:
			amount = execution_id.mobbex_total
			if execution_id.mobbex_created:
				payment_date = execution_id.mobbex_created
		invoice_date = datetime.now()
		fpcmc_values = {
			'partner_id': partner_id.id,
			'company_id': self.company_id.id,
		}
		multi_cobro_id = self.env['financiera.prestamo.cuota.multi.cobro'].create(fpcmc_values)
		partner_id.multi_cobro_ids = [multi_cobro_id.id]
		self.punitorio_fecha_actual = payment_date
		if self.saldo > 0:
			self.confirmar_cobrar_cuota(payment_date, journal_id, amount, multi_cobro_id)
			if len(multi_cobro_id.payment_ids) > 0:
				if execution_id:
					execution_id.mobbex_payment_id = multi_cobro_id.payment_ids[0]
		# Facturacion cuota
		if not self.facturada:
			fpcmf_values = {
				'invoice_type': 'interes',
				'company_id': self.company_id.id,
			}
			multi_factura_id = self.env['financiera.prestamo.cuota.multi.factura'].create(fpcmf_values)
			self.facturar_cuota(invoice_date, factura_electronica, multi_factura_id, multi_cobro_id)
			if multi_factura_id.invoice_amount == 0:
				multi_factura_id.unlink()
		if self.punitorio_a_facturar > 0:
			fpcmf_values = {
				'invoice_type': 'punitorio',
				'company_id': self.company_id.id,
			}
			multi_factura_punitorio_id = self.env['financiera.prestamo.cuota.multi.factura'].create(fpcmf_values)
			self.facturar_punitorio_cuota(invoice_date, factura_electronica, multi_factura_punitorio_id, multi_cobro_id)
			if multi_factura_punitorio_id.invoice_amount == 0:
				multi_factura_punitorio_id.unlink()

