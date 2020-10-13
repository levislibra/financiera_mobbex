# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

import json
class FinancieraMobbexWebhookController(http.Controller):

	@http.route("/financiera.mobbex/webhook", type="json", auth="public", method=["POST"])
	def webhook_listener(self, **kwargs):
		print("WEBHOOK EJECUTADO!")
		print("kwards: ", kwargs)
		print("kwards: ", kwargs['type'])
		webhook_type = None
		if 'type' in kwargs:
			webhook_type = kwargs['type']
		if webhook_type == "subscription:registration":
			print("Webhook: Nueva Suscripción")
			_id = kwargs['data']['subscriber']['reference']
			print("_id: ", _id)
			prestamo_id = request.env['financiera.prestamo'].sudo().browse(int(_id))
			print("prestamo: ", prestamo_id)
			prestamo_id.mobbex_suscripcion_exitosa()
		elif webhook_type == "subscription:change_source":
			print("Webhook: Cambio de Método de Pago")
		elif webhook_type == "subscription:execution":
			print("Webhook: Suscripción Ejecutada")
			_id = kwargs['data']['subscriber']['reference']
			print("_id: ", _id)
			cuota_id = request.env['financiera.prestamo.cuota'].sudo().browse(int(_id))
			print("cuota: ", cuota_id)
			print("MONTO: ", kwargs['data']['payment']['total'])
			cuota_id.mobbex_read_execution(kwargs['data'])
		elif webhook_type == "subscription:subscriber:suspended":
			print("Webhook: Suscriptor Suspendido")
		elif webhook_type == "subscription:subscriber:active":
			print("Webhook: Suscriptor Activado")
		return json.dumps("OK")

