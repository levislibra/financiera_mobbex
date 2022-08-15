# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
from datetime import datetime, timedelta, date
import requests

_logger = logging.getLogger(__name__)

URL_SUSCRIPTIONS = 'https://api.mobbex.com/p/subscriptions/'
TIME_BETWEEN_EXECUTION = 6
URL_OPERATIONS = 'https://api.mobbex.com/p/operations'

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

	@api.model
	def _cron_update_aprobados(self):
		print("_cron_update_aprobados")
		company_obj = self.pool.get('res.company')
		company_ids = [3, 10] #company_obj.search(self.env.cr, self.env.uid, [])
		for _id in company_ids:
			company_id = company_obj.browse(self.env.cr, self.env.uid, _id)
			headers = {
				'x-api-key': company_id.mobbex_id.api_key,
				'x-access-token': company_id.mobbex_id.access_token,
			}
			from_day = datetime.datetime.now() - datetime.timedelta(days=15)
			created = datetime.datetime.now()
			page = 0
			while (from_day < created):
				params = {
					'page': page,
					'limit': 50,
					'status': 200,
				}
				r = requests.get(URL_OPERATIONS, params=params, headers=headers)
				response = r.json()
				if 'result' in response and response['result'] == True and 'data' in response:
					data = response['data']
					if 'docs' in data:
						docs = data['docs']
						print('len docs: ' + str(len(docs)))
						for doc in docs:
							if 'reference' in doc:
								print('reference: ', doc['reference'])
								print('status: ', doc['status'])
								print('total: ', doc['total'])
								created = datetime.datetime.strptime(doc['created'].split('T')[0], "%Y-%m-%d")
								print('created: ', created)
								print('context.value: ', doc['context']['value'])
								print('context.name: ', doc['context']['name'])
								_id = doc['reference'].split('_')[0]
								if cuota_id.state == 'activa':
									if doc['context']['value'] == 'plugin.value.subscriptions:exec':
										cuota_id = self.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
										cuota_id.mobbex_read_execution_aprobado(doc)
										_logger.info('Mobbex: nuevo debito procesado.')
									elif doc['context']['value'] == 'plugin.value.payment_order:web':
										orden_pago_id = self.env['financiera.mobbex.orden.pago'].sudo().browse(int(_id))
										orden_pago_id.mobbex_orden_pago_read_execution_aprobado(doc)
										_logger.info('Mobbex: nueva orden de pago procesada.')
							else:
								_logger.warning('Mobbex: No existe reference de cuota.')
							if from_day >= created:
								break
						if len(docs) == 0:
							break
				page += 1