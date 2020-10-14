# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

import json
class FinancieraMobbexWebhookController(http.Controller):

	@http.route("/financiera.mobbex/webhook", type="json", auth="public", csrf=False, method=["POST"])
	def webhook_listener(self, **kwargs):
		webhook_type = None
		if 'type' in kwargs:
			webhook_type = kwargs['type']
		if webhook_type == "subscription:registration":
			_id = kwargs['data']['subscriber']['reference']
			prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
			prestamo_id.mobbex_suscripcion_exitosa()
		elif webhook_type == "subscription:change_source":
			print("Webhook: Cambio de Método de Pago")
		elif webhook_type == "subscription:execution":
			_id = kwargs['data']['subscriber']['reference']
			cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
			cuota_id.mobbex_read_execution(kwargs['data'])
		elif webhook_type == "subscription:subscriber:suspended":
			print("Webhook: Suscriptor Suspendido")
		elif webhook_type == "subscription:subscriber:active":
			print("Webhook: Suscriptor Activado")
		return json.dumps("OK")

