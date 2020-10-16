# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta

import requests
import json

URL_SUSCRIPTIONS = 'https://api.mobbex.com/p/subscriptions/'

WEBHOOK_DIR = "https://cloudlibrasoft.com/financiera.mobbex/webhook"
# WEBHOOK_DIR = "http://localhost:8069/financiera.mobbex/webhook"

class ExtendsFinancieraPrestamo(models.Model):
	_inherit = 'financiera.prestamo' 
	_name = 'financiera.prestamo'

	mobbex_id = fields.Many2one('financiera.mobbex.config', related='company_id.mobbex_id', readonly=True)
	mobbex_debito_automatico = fields.Boolean('Mobbex - Debito automatico')
	# Suscription
	mobbex_suscripcion_id = fields.Char('Mobbex - Suscripcion ID')
	mobbex_suscripcion_shorten_url = fields.Char('Mobbex - Url para la suscripcion')
	# Suscriptor
	mobbex_suscriptor_id = fields.Char('Mobbex - Suscriptor ID')
	mobbex_suscriptor_sourceUrl = fields.Char('Mobbex - Url para el suscriptor')
	mobbex_suscriptor_subscriberUrl = fields.Char('Mobbex - Url para el control')
	mobbex_suscripcion_suscriptor_confirm = fields.Boolean('Mobbex - Suscripcion exitosa')

	@api.one
	def enviar_a_autorizado(self):
		super(ExtendsFinancieraPrestamo, self).enviar_a_autorizado()
		if self.mobbex_debito_automatico:
			self.mobbex_create_suscription()
			self.mobbex_create_suscriptor()

	@api.one
	def mobbex_create_suscription(self):
		url = URL_SUSCRIPTIONS
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		features = []
		if self.mobbex_id.validate_id:
			features.append("validate_id")
		if self.mobbex_id.accept_no_funds:
			features.append("accept_no_funds")
		name = self.partner_id.name
		name += " ("+str(self.partner_id.main_id_number)+"): "
		name += self.name
		body = {
			'total': 0,
			'currency': 'ARS',
			'type': 'manual',
			'name': name,
			'limit': 0,
			'webhook': WEBHOOK_DIR,
			'return_url': self.mobbex_id.return_url,
			'features': features,
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		data = r.json()
		if 'result' in data and data['result'] == True:
			self.mobbex_suscripcion_id = data['data']['uid']
			self.mobbex_suscripcion_shorten_url = data['data']['shorten_url']

	@api.one
	def mobbex_obtener_suscription(self):
		url = URL_SUSCRIPTIONS+self.mobbex_suscripcion_id
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		r = requests.get(url, headers=headers)

	@api.one
	def mobbex_activate_suscription(self):
		url = URL_SUSCRIPTIONS+self.mobbex_suscripcion_id+'/action/activate'
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		r = requests.get(url, headers=headers)


	@api.one
	def mobbex_create_suscriptor(self):
		url = URL_SUSCRIPTIONS+self.mobbex_suscripcion_id+'/subscriber'
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		current_day = datetime.now()
		body = {
			'customer': {
				'identification': str(self.partner_id.main_id_number),
				'email': self.partner_id.email,
				'name': self.partner_id.name,
				'phone': str(self.partner_id.mobile),
			},
			'reference': str(self.id),
			'startDate': {
				'day': current_day.day,
				'month': current_day.month-1,
			},
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		data = r.json()
		if 'result' in data and data['result'] == True:
			self.mobbex_suscriptor_id = data['data']['uid']
			self.mobbex_suscriptor_sourceUrl = data['data']['sourceUrl']
			self.mobbex_suscriptor_subscriberUrl = data['data']['subscriberUrl']

	@api.one
	def mobbex_suscripcion_exitosa(self):
		self.mobbex_suscripcion_suscriptor_confirm = True