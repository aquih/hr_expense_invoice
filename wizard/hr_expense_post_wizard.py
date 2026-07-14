# -*- encoding: utf-8 -*-

from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_amount

import logging

class HrExpensePostWizard(models.TransientModel):
    _inherit = 'hr.expense.post.wizard'

    def action_post_entry(self):
        result = super().action_post_entry()
        logging.warning(result)

        gastos = self.env['hr.expense'].browse(self.env.context['active_ids'])
        lineas_por_pagar = gastos.factura_id.line_ids.filtered(lambda l: l.account_type == 'liability_payable' and not l.reconciled)

        if lineas_por_pagar.exists():
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

            for g in gastos.filtered(lambda g: g.factura_id.exists()):
                total_factura = sum(g.factura_id.line_ids.filtered(lambda l: l.account_type == 'liability_payable' and not l.reconciled).mapped('credit'))
                if float_compare(g.total_amount, total_factura, precision_rounding=g.currency_id.rounding) != 0:
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
