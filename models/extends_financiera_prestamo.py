# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from openerp.exceptions import UserError, ValidationError

import requests
import json

URL_SUSCRIPTIONS = 'https://api.mobbex.com/p/subscriptions/'

WEBHOOK_DIR = "https://cloudlibrasoft.com/financiera.mobbex/webhook"

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
	mobbex_suscripcion_suscriptor_attempts = fields.Integer('Mobbex - Intentos de suscripcion')
	# Otros
	mobbex_days_execute_on_expiration = fields.Integer('Desplazamiento de dias para primer debito con respecto al vencimiento', compute='_compute_mobbex_days_execute_on_expiration')

	@api.model
	def default_get(self, fields):
		rec = super(ExtendsFinancieraPrestamo, self).default_get(fields)
		if len(self.env.user.company_id.mobbex_id) > 0:
			rec.update({
				'mobbex_debito_automatico': self.env.user.company_id.mobbex_id.set_default_payment,
			})
		return rec


	@api.one
	def enviar_a_autorizado(self):
		super(ExtendsFinancieraPrestamo, self).enviar_a_autorizado()
		if self.mobbex_debito_automatico:
			if not self.mobbex_suscripcion_id or not self.mobbex_suscriptor_id:
				self.mobbex_create_suscription()
				self.mobbex_create_suscriptor()
				self.mobbex_suscripcion_suscriptor_confirm = False

	@api.one
	def mobbex_create_suscription(self):
		url = URL_SUSCRIPTIONS
		headers = {
			'x-api-key': self.mobbex_id.api_key,
			'x-access-token': self.mobbex_id.access_token,
			'content-type': 'application/json',
		}
		features = ["no_email"]
		if self.mobbex_id.validate_id:
			features.append("validate_id")
		if self.mobbex_id.accept_no_funds:
			features.append("accept_no_funds")
		name = self.partner_id.name
		if not self.partner_id.dni:
			raise UserError("Error en el DNI o CUIT del cliente. Controle espacios en blanco delante y al final del mismo.")
		name += " ("+self.partner_id.dni+"): "
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
			'options': {
          'button': True,
          'embed': True,
          'domain': self.company_id.portal_url,
			}
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		data = r.json()
		if 'result' in data and data['result'] == True:
			self.mobbex_suscripcion_id = data['data']['uid']
			self.mobbex_suscripcion_shorten_url = data['data']['shorten_url']

	@api.one
	def button_mobbex_create_suscription(self):
		self.mobbex_create_suscription()
		self.mobbex_suscriptor_id = None
		self.mobbex_suscriptor_sourceUrl = None
		self.mobbex_suscriptor_subscriberUrl = None
		self.mobbex_suscripcion_suscriptor_confirm = False


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
		if self.partner_id.dni == False:
			raise UserError("Error en DNI del cliente.")
		body = {
			'customer': {
				'identification': self.partner_id.dni,
				'email': self.partner_id.email,
				'name': self.partner_id.name,
				'phone': str(self.partner_id.mobile),
			},
			'reference': str(self.id),
			'startDate': {
				'day': current_day.day,
				'month': current_day.month,
			},
		}
		r = requests.post(url, data=json.dumps(body), headers=headers)
		data = r.json()
		if 'result' in data and data['result'] == True:
			self.mobbex_suscriptor_id = data['data']['uid']
			self.mobbex_suscriptor_sourceUrl = data['data']['sourceUrl']
			self.mobbex_suscriptor_subscriberUrl = data['data']['subscriberUrl']

	@api.one
	def mobbex_suscripcion_exitosa(self, payment_status):
		print("mobbex_suscripcion_exitosa")
		print("payment_status: ", payment_status)
		if self.mobbex_id.accept_no_funds:
			self.mobbex_suscripcion_suscriptor_confirm = True
		elif payment_status == 200:
			self.mobbex_suscripcion_suscriptor_confirm = True

	@api.one
	def _compute_mobbex_days_execute_on_expiration(self):
		self.mobbex_days_execute_on_expiration = abs(self.mobbex_id.days_execute_on_expiration)

