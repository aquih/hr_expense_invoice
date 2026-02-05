# -*- encoding: utf-8 -*-

from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_amount

import logging

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    factura_id = fields.Many2one('account.move', string="Factura", domain="[('state','=','posted'), ('move_type', '=', 'in_invoice')]", check_company=True)

    @api.onchange('factura_id')
    def _onchange_factura_id(self):
        if self.factura_id:
            if not self.product_has_cost:
                self.tax_ids = [Command.clear()]
                self.currency_id = self.factura_id.currency_id
                self.total_amount_currency = self.factura_id.amount_total
                self.currency_rate = 1 / max([l.currency_rate for l in self.factura_id.invoice_line_ids])
            else:
                self.factura_id = False
                return {
                    'warning': {'title': 'Producto con costo', 'message': 'No se pueden relacionar facturas cuando el producto de gasto tiene un costo. El campo de factura se ha dejado vacío.'},
                }
            
    @api.onchange('product_has_cost')
    def _onchange_product_has_cost(self):
        if self.product_has_cost and self.factura_id:
            self.factura_id = False
            return {
                    'warning': {'title': 'Producto con costo', 'message': 'No se pueden relacionar facturas cuando el producto de gasto tiene un costo. El campo de factura se ha dejado vacío.'},
                }