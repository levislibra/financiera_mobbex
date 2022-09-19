# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import logging
import json

_logger = logging.getLogger(__name__)
class FinancieraMobbexWebhookController(http.Controller):

	@http.route("/financiera.mobbex/webhook", type='json', auth='none', cors='*', csrf=False)#, auth="public", csrf=False)
	def webhook_listener(self, **post):
		# _logger.info('Mobbex: nuevo webhook.')
		response = request.jsonrequest
		webhook_type = None
		if 'type' in response:
			webhook_type = response.get('type')
			# _logger.info('Mobbex: tipo ' + webhook_type)
		data = response.get('data')
		if webhook_type == "subscription:registration":
			if 'subscriber' in data and 'reference' in data['subscriber']:
				_id = data['subscriber']['reference']
				_logger.info('Mobbex: subscriber id '+_id)
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				payment_status = '200'
				if 'payment' in data and 'status' in data['payment'] and 'code' in data['payment']['status']:
					payment_status = data['payment']['status']['code']
				_logger.info('Payment status: ' + payment_status)
				prestamo_id.mobbex_suscripcion_exitosa(payment_status)
				_logger.info('Mobbex: Nueva suscripcion.')
			else:
				_logger.warning('Mobbex: No existe reference.')
		elif webhook_type == "subscription:change_source":
			if 'subscriber' in data and 'reference' in data['subscriber']:
				_id = data['subscriber']['reference']
				_logger.info('Mobbex: subscriber id '+_id)
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				payment_status = '200'
				if 'payment' in data and 'status' in data['payment'] and 'code' in data['payment']['status']:
					payment_status = data['payment']['status']['code']
				_logger.info('Payment status: ' + payment_status)
				prestamo_id.mobbex_suscripcion_exitosa(payment_status)
				_logger.info('Mobbex: cambio Metodo de Pago.')
			else:
				_logger.warning('Mobbex: No existe reference.')
		elif webhook_type == "subscription:execution":
			if 'payment' in data and 'reference' in data['payment']:
				_id = data['payment']['reference'].split('_')[0]
				cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
				cuota_id.mobbex_read_execution(data)
				_logger.info('Mobbex: nuevo debito procesado.')
			else:
				_logger.warning('Mobbex: No existe reference de cuota.')
		elif webhook_type == "subscription:subscriber:suspended":
			_logger.info('Mobbex: suscriptor suspendido.')
		elif webhook_type == "subscription:subscriber:active":
			_logger.info('Mobbex: suscriptor activado.')
		elif webhook_type == "payment_order":
			if 'payment' in data and 'reference' in data['payment']:
				_id = data['payment']['reference'].split('_')[0]
				orden_pago_id = request.env['financiera.mobbex.orden.pago'].sudo().browse(int(_id))
				orden_pago_id.mobbex_orden_pago_read_execution(data)
				_logger.info('Mobbex: nueva orden de pago procesada.')
			else:
				_logger.warning('Mobbex: No existe reference de cuota.')

		return json.dumps("OK")

