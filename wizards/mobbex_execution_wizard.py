# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import math
import threading

TIME_BETWEEN_EXECUTION = 4

class MobbexExecutionWizard(models.TransientModel):
	_name = 'mobbex.execution.wizard'
	
	@api.multi
	def confirmar_ejecucion(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		count = 0
		for _id in active_ids:
			execution_id = self.env['financiera.mobbex.execution'].browse(_id)
			cuota_id = execution_id.mobbex_cuota_id
			# threading.Timer((count+1) * TIME_BETWEEN_EXECUTION, cuota_id.mobbex_subscriber_execution).start()
			cuota_id.mobbex_subscriber_execution()
			count += 1
