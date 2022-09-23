# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
from datetime import datetime, timedelta, date
import requests

_logger = logging.getLogger(__name__)

URL_OPERATIONS = 'https://api.mobbex.com/p/operations'

class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	mobbex_id = fields.Many2one('financiera.mobbex.config', 'Configuracion Mobbex')

	@api.one
	def mobbex_update_aprobados(self):
		if self.mobbex_id:
			headers = {
				'x-api-key': self.mobbex_id.api_key,
				'x-access-token': self.mobbex_id.access_token,
			}
			from_day = datetime.now() - timedelta(days=self.mobbex_id.days_check_update_aprobados)
			created = datetime.now()
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
					print('result')
					data = response['data']
					if 'docs' in data:
						print('docs')
						docs = data['docs']
						for doc in docs:
							if 'reference' in doc:
								created = datetime.strptime(doc['created'].split('T')[0], "%Y-%m-%d")
								_id = doc['reference'].split('_')[0]
								if doc['context']['value'] == 'plugin.value.subscriptions:exec':
									cuota_id = self.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
									if cuota_id.state == 'activa':
										cuota_id.mobbex_read_execution_aprobado(doc)
										_logger.info('Mobbex: nuevo debito procesado.')
								elif doc['context']['value'] == 'plugin.value.payment_order:web':
									orden_pago_id = self.env['financiera.mobbex.orden.pago'].sudo().browse(int(_id))
									if orden_pago_id.state != 'cobrada':
										orden_pago_id.mobbex_orden_pago_read_execution_aprobado(doc)
										_logger.info('Mobbex: nueva orden de pago procesada.')
							else:
								_logger.warning('Mobbex: No existe reference de cuota.')
							if from_day >= created:
								break
						if len(docs) <= 1:
							break
					else:
						break
				else:
					break
				page += 1