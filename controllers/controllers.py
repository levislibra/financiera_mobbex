# -*- coding: utf-8 -*-
from openerp import http

# class FinancieraMobbex(http.Controller):
#     @http.route('/financiera_mobbex/financiera_mobbex/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/financiera_mobbex/financiera_mobbex/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('financiera_mobbex.listing', {
#             'root': '/financiera_mobbex/financiera_mobbex',
#             'objects': http.request.env['financiera_mobbex.financiera_mobbex'].search([]),
#         })

#     @http.route('/financiera_mobbex/financiera_mobbex/objects/<model("financiera_mobbex.financiera_mobbex"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('financiera_mobbex.object', {
#             'object': obj
#         })