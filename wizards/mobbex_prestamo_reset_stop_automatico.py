# -*- coding: utf-8 -*-

from openerp import models, fields, api

class MobbexPrestamoResetStopWizard(models.TransientModel):
	_name = 'mobbex.prestamo.reset.stop.wizard'
	
	@api.multi
	def reset_stop_automatico(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		for _id in active_ids:
			prestamo_id = self.env['financiera.prestamo'].browse(_id)
			prestamo_id.write({'mobbex_stop_automatico': False})
