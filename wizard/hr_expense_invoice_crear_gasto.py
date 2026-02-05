# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
      
class HRExpenseInvoiceCrearGasto(models.TransientModel):
    _name = 'hr.expense.invoice.crear_gasto'
    _description = 'Crear gastos desde factura'
    
    empleado_id = fields.Many2one('hr.employee', required=True)
    
    def action_crear_gasto(self):
        active_ids = self.env.context.get('active_ids')

        facturas = self.env['account.move'].browse(active_ids)
        gastos = facturas.crear_gasto(self.empleado_id.id)

        return {
            'name': _('Gasto'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'context': {'create': False},
            'view_mode': 'list,form',
            'domain': [('id', 'in', gastos.ids)],
        }
