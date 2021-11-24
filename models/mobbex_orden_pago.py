# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
import logging
import requests
import json

_logger = logging.getLogger(__name__)

URL_ORDEN_PAGO = "https://api.mobbex.com/p/payment_order"

WEBHOOK_DIR = "https://cloudlibrasoft.com/financiera.mobbex/webhook"

class FinancieraMobbexOrdenPago(models.Model):
	_name = 'financiera.mobbex.orden.pago'

	_order = 'id desc'
	name = fields.Char('Nombre')
	partner_id = fields.Many2one('res.partner')
	mobbex_id = fields.Many2one('financiera.mobbex.config', related='company_id.mobbex_id', readonly=True)
	cuota_ids = fields.Many2many('financiera.prestamo.cuota', 'financiera_mobbex_cuota_mobbexordenpago_rel', 'cuota_id', 'orden_id', string='Cuotas')
	total = fields.Float('Total')
	descripcion = fields.Char('Descripcion')
	state = fields.Selection([('borrador', 'Borrador'), ('abierta', 'Abierta'), ('cobrada', 'Cobrada')], 'Estado', default='borrador')
	company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env['res.company']._company_default_get('financiera.mobbex.orden.pago'))

	payment_id = fields.Many2one('account.payment', 'Comprobante de pago')
	mobbex_uid = fields.Char('Mobbex UID')
	mobbex_shorten_url = fields.Char('Mobbex url corta de pago')
	mobbex_url = fields.Char('Mobbex url de pago')

	@api.model
	def create(self, values):
		rec = super(FinancieraMobbexOrdenPago, self).create(values)
		rec.update({
			'name': "ORDEN/PAGO/" + str(rec.id).zfill(8),
		})
		return rec

	@api.one
	def calcular_total_y_detalle(self):
		total = 0
		descripcion = "Pago de cuotas: "
		for cuota_id in self.cuota_ids:
			total += cuota_id.saldo
			descripcion += cuota_id.name + ", "
		self.total = total
		self.descripcion = descripcion

	@api.one
	def mobbex_crear_orden_pago(self):
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		self.calcular_total_y_detalle()
		current_day = datetime.now()
		body = {
			'reference': str(self.id),
			'total': self.total,
			'description': self.descripcion,
			"due": {
				"day": current_day.day,
				"month": current_day.month,
				"year": current_day.year,
			},
			'customer': {
				'email': self.partner_id.email,
				'identification': self.partner_id.dni,
				'name': self.partner_id.name,
				'phone': str(self.partner_id.mobile),
			},
			# 'multicard': True,
			'webhook': WEBHOOK_DIR,
		}
		r = requests.post(URL_ORDEN_PAGO, data=json.dumps(body), headers=headers)
		data = r.json()
		if 'result' in data and data['result'] == True:
			self.mobbex_uid = data['data']['uid']
			self.mobbex_shorten_url = data['data']['shorten_url']
			self.mobbex_url = data['data']['url']
			self.state = 'abierta'

	@api.one
	def mobbex_orden_pago_read_execution(self, post):
		_logger.info("mobbex_orden_pago_read_execution")
		_logger.info("POST!!!")
		_logger.info(post)
		_logger.info("*******")
		if 'data[payment][status][code]' in post and post['data[payment][status][code]'] == 200:
			for cuota_id in self.cuota_ids:
				cuota_id.mobbex_cobrar_cuota()
			self.state = 'cobrada'