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
        if self.product_has_cost:
            self.factura_id = False
            return {
                    'warning': {'title': 'Producto con costo', 'message': 'No se pueden relacionar facturas cuando el producto de gasto tiene un costo. El campo de factura se ha dejado vacío.'},
                }

class HrExpensePostWizard(models.TransientModel):
    _inherit = 'hr.expense.post.wizard'

    def action_post_entry(self):
        result = super().action_post_entry()

        gastos = self.env['hr.expense'].browse(self.env.context['active_ids'])
        lineas_por_pagar = gastos.factura_id.line_ids.filtered(lambda l: l.account_type == 'liability_payable' and not l.reconciled)

        lineas = []
        for p in lineas_por_pagar:
            lineas.append(Command.create({
                'name': p.name,
                'ref': p.ref,
                'partner_id': p.partner_id.id,
                'debit': p.credit,
                'credit': 0,
                'account_id': p.account_id.id,
            }))

        for g in gastos:
            total_factura = sum(g.factura_id.line_ids.filtered(lambda l: l.account_type == 'liability_payable' and not l.reconciled).mapped('credit'))
            if g.total_amount != total_factura:
                monto_gasto = format_amount(self.env, g.total_amount, g.company_currency_id, lang_code=self.env.lang)
                monto_factura = format_amount(self.env, total_factura, g.company_currency_id, lang_code=self.env.lang)
            
                raise ValidationError(f"El gasto {g.name} ({monto_gasto}) y la factura {g.factura_id.name} ({monto_factura}) no tienen el mismo total.")

            lineas.append(Command.create({
                'name': g.name,
                'ref': g.name,
                'partner_id': g.employee_id.sudo().work_contact_id.id,
                'debit': 0,
                'credit': g.total_amount,
                'account_id': g.account_id.id,
            }))

        diarios = self.env['account.journal'].search([('type','=','general')])
        misc = diarios.filtered(lambda r: r.code == 'MISC')
        
        diario = diarios[0]
        if len(misc) > 0:
            diario = misc[0]
            
        movimiento = self.env['account.move'].create({
            'journal_id': diario.id,
            'date': self.accounting_date,
            'ref': 'Conciliacion manual: '+', '.join(gastos.mapped('name')),
            'move_type': 'entry',
            'line_ids': lineas
        })
        movimiento.action_post()
        
        i = 0
        for l in lineas_por_pagar:
            (l | movimiento.line_ids[i]).reconcile()
            i += 1
        
        return result
