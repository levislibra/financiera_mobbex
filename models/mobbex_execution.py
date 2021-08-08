# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraMobbexExecution(models.Model):
	_name = 'financiera.mobbex.execution'

	_order = 'id desc'
	mobbex_id = fields.Many2one('financiera.mobbex.config', related='company_id.mobbex_id', readonly=True)
	mobbex_cuota_id = fields.Many2one('financiera.prestamo.cuota', 'Cuota')
	partner_id = fields.Many2one('res.partner', related='mobbex_cuota_id.partner_id', readonly=True)
	mobbex_payment_id = fields.Many2one('account.payment', 'Comprobante de pago')
	company_id = fields.Many2one('res.company', 'Empresa')
	mobbex_ejecucion_id = fields.Char('Ejecucion')
	mobbex_status_code = fields.Char('Codigo')
	mobbex_status_text = fields.Char('Text')
	mobbex_status_message = fields.Char('Mensaje')
	mobbex_total = fields.Float('Total')
	mobbex_currency_code = fields.Char('Codigo de moneda')
	mobbex_currency_text = fields.Char('Texto de moneda')
	mobbex_source_name = fields.Char('Tarjeta')
	mobbex_source_type = fields.Char('Tipo de tajeta')
	mobbex_source_number = fields.Char('Numero de tarjeta')

