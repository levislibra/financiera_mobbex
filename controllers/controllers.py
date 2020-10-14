# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import logging

import json

_logger = logging.getLogger(__name__)
class FinancieraMobbexWebhookController(http.Controller):

	@http.route("/financiera.mobbex/webhook", type="http", auth="public", csrf=False, method=["POST"])
	def webhook_listener(self, **kwargs):
		_logger.info('Mobbex: nuevo webhook.')
		webhook_type = None
		if 'type' in kwargs:
			webhook_type = kwargs['type']
			_logger.info('Mobbex: tipo '+kwargs['type'])
		if webhook_type == "subscription:registration":
			if 'data' in kwargs and 'subscriber' in kwargs['data'] and 'reference' in kwargs['data']['subscriber']:
				_id = kwargs['data']['subscriber']['reference']
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				prestamo_id.mobbex_suscripcion_exitosa()
				_logger.info('Mobbex: Nueva suscripcion.')
			else:
				_logger.info('Mobbex: No existe reference.')
				print("kwargs: ", kwargs.__str__)
				print("kwargs: ", kwargs)
				print("kwargs: ", kwargs['data'])
		elif webhook_type == "subscription:change_source":
			_logger.info('Mobbex: cambio Metodo de Pago.')
		elif webhook_type == "subscription:execution":
			_id = kwargs['data']['subscriber']['reference']
			cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
			cuota_id.mobbex_read_execution(kwargs['data'])
			_logger.info('Mobbex: registrando nuevo debito.')
		elif webhook_type == "subscription:subscriber:suspended":
			_logger.info('Mobbex: suscriptor suspendido.')
		elif webhook_type == "subscription:subscriber:active":
			_logger.info('Mobbex: suscriptor activado.')
		return json.dumps("OK")

