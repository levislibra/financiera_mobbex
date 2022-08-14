# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import logging
import yaml
import json

_logger = logging.getLogger(__name__)
class FinancieraMobbexWebhookController(http.Controller):

	@http.route("/financiera.mobbex/webhook", type='json', auth='none', cors='*', csrf=False)#, auth="public", csrf=False)
	def webhook_listener(self, **post):
		_logger.info('Mobbex: nuevo webhook.')
		_logger.info(post)
		_logger.info('Mobbex: ++++++++++++++')
		webhook_type = None
		if 'type' in post.keys():
			webhook_type = post.get('type')
			_logger.info('Mobbex: tipo '+post.get('type'))
		if webhook_type == "subscription:registration":
			if 'data[subscriber][reference]' in post:
				_id = post['data[subscriber][reference]']
				_logger.info('Mobbex: subscriber id '+_id)
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				payment_status = '200'
				if 'data[payment][status][code]' in post:
					payment_status = post['data[payment][status][code]']
				_logger.info('Payment status: ' + payment_status)
				prestamo_id.mobbex_suscripcion_exitosa(payment_status)
				_logger.info('Mobbex: Nueva suscripcion.')
			else:
				_logger.warning('Mobbex: No existe reference.')
		elif webhook_type == "subscription:change_source":
			if 'data[subscriber][reference]' in post:
				_id = post['data[subscriber][reference]']
				_logger.info('Mobbex: subscriber id '+_id)
				prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
				payment_status = '200'
				if 'data[payment][status][code]' in post:
					payment_status = post['data[payment][status][code]']
				_logger.info('Payment status: ' + payment_status)
				prestamo_id.mobbex_suscripcion_exitosa(payment_status)
				_logger.info('Mobbex: cambio Metodo de Pago.')
			else:
				_logger.warning('Mobbex: No existe reference.')
		elif webhook_type == "subscription:execution":
			# pass
			if 'data[payment][reference]' in post:
				_id = post['data[payment][reference]'].split('_')[0]
				cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
				cuota_id.mobbex_read_execution(post)
				_logger.info('Mobbex: nuevo debito procesado.')
			else:
				_logger.warning('Mobbex: No existe reference de cuota.')
		elif webhook_type == "subscription:subscriber:suspended":
			_logger.info('Mobbex: suscriptor suspendido.')
		elif webhook_type == "subscription:subscriber:active":
			_logger.info('Mobbex: suscriptor activado.')
		elif webhook_type == "payment_order":
			if 'data[payment][reference]' in post:
				_id = post['data[payment][reference]'].split('_')[0]
				orden_pago_id = request.env['financiera.mobbex.orden.pago'].sudo().browse(int(_id))
				orden_pago_id.mobbex_orden_pago_read_execution(post)
				_logger.info('Mobbex: nueva orden de pago procesada.')
			else:
				_logger.warning('Mobbex: No existe reference de cuota.')

		return json.dumps("OK")

