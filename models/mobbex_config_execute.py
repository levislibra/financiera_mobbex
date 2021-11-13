# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta, date

class FinancieraMobbexConfigExecute(models.Model):
	_name = 'financiera.mobbex.config.execute'

	_order = 'priority asc'
	name = fields.Char('Nombre')
	config_id = fields.Many2one('financiera.mobbex.config', 'Config')
	activo = fields.Boolean('Activo')
	priority = fields.Integer('Prioridad', help='0 para la maxima prioridad y 10 para la menor')
	interval_number = fields.Integer('Número de intervalos', help='Repetir cada x.')
	interval_type = fields.Selection([
		# ('minutes', 'Minutos'), ('hours', 'Horas'), 
		('work_days', 'Días laborables'), ('days', 'Días'), ('weeks', 'Semanas'), ('months', 'Meses')], 'Unidad de intervalo')
	numbercall = fields.Integer('Número de ejecuciones', help='Cuantas veces se llama a este metodos, un numero negativo indica sin limite.')
	nextcall = fields.Datetime('Siguiente fecha de ejecución')
	amount = fields.Float('Monto', help='Cero o negativo para ejecutar el saldo de la cuota.')
	ir_cron_id = fields.Many2one('ir.cron', 'Cron')
	company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env['res.company']._company_default_get('financiera.mobbex.config.execute'))
	company_name = fields.Char('Nombre de la Empresa', related='company_id.name', readonly=True)

	def get_values(self):
		values = {
			'name': self.company_name + ' - ' + self.name,
			'user_id': 1,
			'priority': self.priority,
			'active': self.activo,
			'interval_number': self.interval_number,
			'interval_type': self.interval_type,
			'numbercall': self.numbercall,
			'doall': False,
			'nextcall': self.nextcall,
			'model': 'financiera.prestamo.cuota',
			'function': '_mobbex_debit_execute_company',
			'args': '(%s,%s)'%((str(self.company_id.id)), str(self.amount)),
		}
		return values

	@api.model
	def create(self, values):
		rec = super(FinancieraMobbexConfigExecute, self).create(values)
		rec.sudo().create_ir_cron_object()
		return rec
	
	@api.multi
	def write(self, values):
		res = super(FinancieraMobbexConfigExecute, self).write(values)
		self.sudo().edit_ir_cron_object()
		return res

	@api.one
	def create_ir_cron_object(self):
		values = self.get_values()
		ir_cron_id = self.sudo().env['ir.cron'].create(values)
		self.ir_cron_id = ir_cron_id.sudo().id
	
	@api.one
	def edit_ir_cron_object(self):
		values = self.get_values()
		self.sudo().ir_cron_id.update(values)
	
	@api.one
	def unlink(self):
		self.sudo().ir_cron_id.unlink()
		return super(FinancieraMobbexConfigExecute, self).unlink()

	@api.one
	def update_nextcall(self):
		if len(self.ir_cron_id) > 0:
			self.nextcall = self.sudo().ir_cron_id.nextcall