# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import logging
import yaml
import json

_logger = logging.getLogger(__name__)
class FinancieraMobbexWebhookController(http.Controller):

	@http.route("/financiera.mobbex/webhook", auth="public", csrf=False)
	def webhook_listener(self, **post):
		_logger.info('Mobbex: nuevo webhook.')
		webhook_type = None
		if 'type' in post.keys():
			webhook_type = post.get('type')
			_logger.info('Mobbex: tipo '+post.get('type'))
		if webhook_type == "subscription:registration":
			if 'data[subscriber][reference]' in post:
				_id = post['data[subscriber][reference]']
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				prestamo_id.mobbex_suscripcion_exitosa()
				_logger.info('Mobbex: Nueva suscripcion.')
			else:
				_logger.warning('Mobbex: No existe reference.')
		elif webhook_type == "subscription:change_source":
			_logger.info('Mobbex: cambio Metodo de Pago.')
		elif webhook_type == "subscription:execution":
			if 'data[subscriber][reference]' in post:
				_id = post['data[subscriber][reference]']
				print("_ID: ", _id)
				cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
				print("cuota_id: ", cuota_id)
				cuota_id.mobbex_read_execution(post)
				_logger.info('Mobbex: nuevo debito procesado.')
			else:
				_logger.warning('Mobbex: No existe reference de cuota.')
		elif webhook_type == "subscription:subscriber:suspended":
			_logger.info('Mobbex: suscriptor suspendido.')
		elif webhook_type == "subscription:subscriber:active":
			_logger.info('Mobbex: suscriptor activado.')

		return json.dumps("OK")

