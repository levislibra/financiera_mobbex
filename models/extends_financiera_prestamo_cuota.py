# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta, date
from dateutil import relativedelta
import logging

import requests
import json

_logger = logging.getLogger(__name__)
URL_SUSCRIPTIONS = 'https://api.mobbex.com/p/subscriptions/'


class ExtendsFinancieraPrestamoCuota(models.Model):
	_inherit = 'financiera.prestamo.cuota' 
	_name = 'financiera.prestamo.cuota'

	mobbex_id = fields.Many2one('financiera.mobbex.config', related='company_id.mobbex_id', readonly=True)
	mobbex_ejecucion_ids = fields.One2many('financiera.mobbex.execution', 'mobbex_cuota_id', 'Ejecuciones')
	mobbex_program_execution_date = fields.Date('Fecha de ejecucion programada')

	@api.model
	def _mobbex_debit_execute(self):
		cr = self.env.cr
		uid = self.env.uid
		fecha_actual = date.today()
		company_obj = self.pool.get('res.company')
		comapny_ids = company_obj.search(cr, uid, [])
		_logger.info('Mobbex: iniciando debito de cuotas.')
		count = 0
		for _id in comapny_ids:
			company_id = company_obj.browse(cr, uid, _id)
			if len(company_id.mobbex_id) > 0:
				mobbex_id = company_id.mobbex_id
				primer_fecha = fecha_actual - relativedelta.relativedelta(days=mobbex_id.days_execute_on_expiration)
				cuotas_obj = self.pool.get('financiera.prestamo.cuota')
				cuotas_ids = cuotas_obj.search(cr, uid, [
					('company_id', '=', company_id.id),
					('prestamo_id.mobbex_debito_automatico', '=', True),
					('prestamo_id.mobbex_suscripcion_suscriptor_confirm', '=', True),
					('state', '=', 'activa'),
					'|', ('fecha_vencimiento', '<=', primer_fecha.__str__()), 
					('fecha_vencimiento', '<=', fecha_actual),
				])
				partner_execute_ids = []
				create_on = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0).strftime("%m/%d/%Y, %H:%M:%S")
				for _id in cuotas_ids:
					cuota_id = cuotas_obj.browse(cr, uid, _id)
					if cuota_id.partner_id.id not in partner_execute_ids:
						execution_obj = self.pool.get('financiera.mobbex.execution')
						execution_ids = execution_obj.search(cr, uid, [
							('mobbex_cuota_id', '=', cuota_id.id),
							('create_date', '>=', create_on),
							('mobbex_status_code', '=', '400')
						])
						if len(execution_ids) == 0:
							cuota_id.mobbex_subscriber_execution()
							partner_execute_ids.append(cuota_id.partner_id.id)
							count += 1
		_logger.info('Mobbex: finalizo el debito de cuotas: %s cuotas ejecutadas', count)
	
	@api.one
	def mobbex_subscriber_execution(self):
		url = URL_SUSCRIPTIONS+self.prestamo_id.mobbex_suscripcion_id
		url += '/subscriber/'+self.prestamo_id.mobbex_suscriptor_id
		url += '/execution/'
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		body = {
			'total': self.saldo,
			'reference': str(self.id),
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		data = r.json()
		if 'result' in data and data['result'] == True:
			pass

	@api.one
	def mobbex_read_execution(self, post):
		values = {
			'company_id': self.company_id.id,
		}
		if 'data[payment][status][code]' in post:
			values['mobbex_status_code'] = post['data[payment][status][code]']
		if 'data[payment][status][text]' in post:
			values['mobbex_status_text'] = post['data[payment][status][text]']
		if 'data[payment][status][message]' in post:
			values['mobbex_status_message'] = post['data[payment][status][message]']
		if 'data[payment][total]' in post:
			values['mobbex_total'] = post['data[payment][total]']
		if 'data[payment][currency][code]' in post:
			values['mobbex_currency_code'] = post['data[payment][currency][code]']
		if 'data[payment][currency][text]' in post:
			values['mobbex_currency_text'] = post['data[payment][currency][text]']
		if 'data[payment][source][name]' in post:
			values['mobbex_source_name'] = post['data[payment][source][name]']
		if 'data[payment][source][type]' in post:
			values['mobbex_source_type'] = post['data[payment][source][type]']
		if 'data[payment][source][number]' in post:
			values['mobbex_source_number'] = post['data[payment][source][type]']
		if 'data[execution][uid]' in post:
			values['mobbex_ejecucion_id'] = post['data[execution][uid]']
		execution_id = self.env['financiera.mobbex.execution'].create(values)
		self.mobbex_ejecucion_ids = [execution_id.id]
		if execution_id.mobbex_status_code == '200':
			self.mobbex_cobrar_cuota(execution_id)

	@api.one
	def mobbex_cobrar_cuota(self, execution_id):
		# Cobro cuota
		cr = self.env.cr
		uid = self.env.uid
		superuser_id = self.pool.get('res.users').browse(cr, uid, 1)
		superuser_id.company_id = self.company_id.id
		payment_date = datetime.now()
		journal_id = self.mobbex_id.journal_id
		factura_electronica = self.mobbex_id.factura_electronica
		partner_id = self.partner_id
		amount = execution_id.mobbex_total
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

