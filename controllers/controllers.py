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
		_logger.info("----A-----")
		_logger.info(post)
		_logger.info("----C-----")
		webhook_type = None
		if 'type' in post.keys():
			webhook_type = post.get('type')
			_logger.info('Mobbex: tipo '+post.get('type'))
		if webhook_type == "subscription:registration":
			if 'data' in post.keys() and 'subscriber' in post.get('data').keys() and 'reference' in post.get('data').get('subscriber').keys():
				_id = post.get('data').get('subscriber').get('reference')
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				prestamo_id.mobbex_suscripcion_exitosa()
				_logger.info('Mobbex: Nueva suscripcion.')
			else:
				_logger.info('Mobbex: No existe reference.')
		elif webhook_type == "subscription:change_source":
			_logger.info('Mobbex: cambio Metodo de Pago.')
		elif webhook_type == "subscription:execution":
			_id = post.get('data').get('subscriber').get('reference')
			cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
			cuota_id.mobbex_read_execution(post.get('data'))
			_logger.info('Mobbex: registrando nuevo debito.')
		elif webhook_type == "subscription:subscriber:suspended":
			_logger.info('Mobbex: suscriptor suspendido.')
		elif webhook_type == "subscription:subscriber:active":
			_logger.info('Mobbex: suscriptor activado.')
		
		print('{}\n{}\r\n{}\r\n\r\n{}'.format(
				'-----------START-----------',
				request.httprequest.method + ' ' + request.httprequest.url,
				'\r\n'.join('{}: {}'.format(k, v) for k, v in request.httprequest.headers.items()),
				request.httprequest.body,
		))
		return json.dumps("OK")

