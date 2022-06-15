# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import date, datetime
import datetime

_STATES = [
    ('draft', 'Draft'),
    ('confirm', 'Confirm'), ('cancel', 'Cancel')
]


class alfolk_expense_personal(models.Model):
    _name = 'alfolk.expense.personal'

    _description = 'Expense Personal'
    _inherit = ['mail.thread']
    _rec_name = 'code'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', store=True,
                                          track_visibility='onchange')
    analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Analytic Tag', store=True,
                                          track_visibility='onchange')

    @api.depends('state')
    def _computemove(self):
        for order in self:
            move = self.env['account.move'].search([('name', '=', order.code)])
            order.move_id = move.id

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry', ondelete='cascade',
        check_company=True, compute='_computemove')

    def _get_valid_liquidity_accounts(self):
        return (
            self.treasury.default_account_id,
            self.treasury.company_id.account_journal_payment_debit_account_id,
            self.treasury.company_id.account_journal_payment_credit_account_id,
            self.treasury.inbound_payment_method_line_ids.payment_account_id,
            self.treasury.outbound_payment_method_line_ids.payment_account_id,
        )

    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        for line in self.move_id.line_ids:
            if line.account_id in self._get_valid_liquidity_accounts():
                liquidity_lines += line
            elif line.account_id.internal_type in (
                    'receivable', 'payable') or line.partner_id == line.company_id.partner_id:
                counterpart_lines += line
            else:
                writeoff_lines += line

        return liquidity_lines, counterpart_lines, writeoff_lines

    def action_open_manual_reconciliation_widget(self):
        ''' Open the manual reconciliation widget for the current payment.
        :return: A dictionary representing an action.
        '''
        self.ensure_one()

        if not self.customer:
            raise UserError(_("Payments without a customer can't be matched"))

        liquidity_lines, counterpart_lines, writeoff_lines = self._seek_for_lines()

        action_context = {'company_ids': self.company_id.ids, 'partner_ids': self.customer.ids}
        if self.payment_type == 'receive_money':
            action_context.update({'mode': 'customers'})
        elif self.payment_type == 'receive_money':
            action_context.update({'mode': 'suppliers'})

        if counterpart_lines:
            action_context.update({'move_line_id': counterpart_lines[0].id})

        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }

    def unlink(self):
        if any(record.state not in ['draft'] for record in self):
            raise UserError(_('Cannot delete a item in post state'))

        return super(alfolk_expense_personal, self).unlink()

    # Fields Defi ne
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency', string="Report Company Currency",
                                          related='company_id.currency_id', readonly=True)

    state = fields.Selection(selection=_STATES, string='Status', index=True, track_visibility='onchange', required=True,
                             copy=False, default='draft', store=True)
    customer = fields.Many2one('res.partner', string='Customer', store=True, index=True, tracking=True)
    amount = fields.Float(string='Amount', store=True, index=True, tracking=True, required=True)
    date = fields.Date(string='Date', store=True, tracking=True, required=True, default=fields.Datetime.now)

    @api.model
    def _getjournalId(self):
        current_user_id = self.env.user

        if current_user_id.has_group('base.user_admin'):
            return [('type', 'in', ('cash', 'bank')),
                    ]
        if not current_user_id.has_group('base.user_admin'):
            return [('id', '=', self.env.user.journal_ids.ids), ('type', 'in', ('cash', 'bank')),
                    ]

    treasury = fields.Many2one('account.journal', string='Treasury', store=True,
                               domain=_getjournalId)
    treasury_to = fields.Many2one('account.journal', string='To Treasury', store=True,
                                  domain="[('type', 'in', ('cash','bank'))]")
    account_to = fields.Many2one('account.account', string='To Account', store=True,
                                 )
    account_id = fields.Many2one('account.account', string='Account', store=True,
                                 )
    account_from = fields.Many2one('account.account', string='From Account', store=True,
                                   )
    code = fields.Char('Reference', size=32, copy=False,
                       store=True,
                       default=lambda self: (" "))
    description = fields.Char(string='Expense For', store=True, index=True, tracking=True)
    note = fields.Char(string='Note', store=True, index=True, tracking=True)
    employee = fields.Many2one('hr.employee', string='Employee', store=True, index=True, tracking=True, )
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, index=True, tracking=True)
    payment_type = fields.Selection([
        ('receive_money', 'Receive Money'),
        ('expense_money', 'Expense Money'), ('transfer_money', 'Transfer Money')],
        string='Type', default='receive_money', store=True, track_visibility='onchange')

    def button_journal_entries(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('name', '=', self.code)],
        }

    @api.constrains('amount')
    def check_amount(self):
        if self.amount <= 0:
            raise ValidationError(_('Amount must be Positive'))

    def confirm(self):
        for expense in self:
            res = self.env['account.move'].search([('name', '=', expense.code)])
            ff = self.env['account.move.line'].search([('move_id', '=', res.id)])
            if res:
                dt = expense.date
                if self.payment_type == 'receive_money':
                    if self.customer:

                        balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                               expense.company_id, dt)
                        debit = credit = balance

                        move = {
                            'date': dt,
                            'ref': expense.note,
                            'line_ids': [(0, 0, {
                                'name': expense.code,
                                'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.treasury.default_account_id.id,

                            }), (0, 0, {
                                'name': expense.code,
                                'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,

                                'account_id': expense.customer.property_account_receivable_id.id,
                                'partner_id': expense.customer.id,

                            })]
                        }
                    else:
                        balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                               expense.company_id, dt)
                        debit = credit = balance
                        move = {
                            'date': dt,
                            'ref': expense.note,
                            'line_ids': [(0, 0, {
                                'name': expense.code,
                                'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.treasury.default_account_id.id,

                            }), (0, 0, {
                                'name': expense.code,
                                'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.account_id.id,
                                'partner_id': expense.customer.id,

                            })]
                        }
                    res.line_ids -= res.line_ids
                    move_id = res.write(move)
                    res.action_post()
                    self.write({'state': 'confirm'})
                elif self.payment_type == 'expense_money':
                    dt = expense.date

                    balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                           expense.company_id, dt)
                    debit = credit = balance
                    if self.customer:
                        move = {
                            'journal_id': expense.treasury.id,
                            'date': dt,
                            'ref': expense.note,
                            'line_ids': [(0, 0, {
                                'name': expense.description,
                                'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.customer.property_account_payable_id.id,
                                'partner_id': expense.customer.id,
                            }), (0, 0, {
                                'name': expense.description,
                                'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.treasury.default_account_id.id,
                                'analytic_account_id': expense.analytic_account_id.id,
                                'analytic_tag_ids': expense.analytic_tag_ids.id,

                            })]
                        }
                    else:
                        move = {
                            'journal_id': expense.treasury.id,
                            'date': dt,
                            'ref': expense.note,
                            'line_ids': [(0, 0, {
                                'name': expense.description,
                                'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.account_id.id,
                                'partner_id': expense.customer.id,
                            }), (0, 0, {
                                'name': expense.description,
                                'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                'account_id': expense.treasury.default_account_id.id,

                            })]
                        }
                    res.line_ids -= res.line_ids
                    move_id = res.write(move)
                    res.action_post()
                    self.write({'state': 'confirm'})
                elif self.payment_type == 'transfer_money':
                    dt = expense.date
                    balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                           expense.company_id, dt)
                    debit = credit = balance
                    move = {
                        # 'journal_id': expense.treasury.id,
                        'date': dt,
                        'ref': expense.note,
                        'line_ids': [(0, 0, {
                            'name': expense.description,
                            'credit': credit,
                            'amount_currency': credit, 'currency_id': expense.currency_id.id,
                            'account_id': expense.account_to.id,
                            'partner_id': expense.customer.id,
                        }), (0, 0, {
                            'name': expense.description,
                            'debit': debit, 'amount_currency': -debit, 'currency_id': expense.currency_id.id,
                            'account_id': expense.account_from.id,

                        })]
                    }
                    res.line_ids -= res.line_ids
                    move_id = res.write(move)
                    res.action_post()
                    self.write({'state': 'confirm'})

            else:
                if self.analytic_account_id and self.analytic_tag_ids:
                    if self.payment_type == 'receive_money':
                        dt = expense.date
                        if self.customer:
                            balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                                   expense.company_id, dt)
                            debit = credit = balance
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.code,
                                    'debit': debit, ''
                                                    'amount_currency': debit,
                                    'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                }), (0, 0, {
                                    'name': expense.code,
                                    'credit': credit,
                                    'amount_currency': -credit,
                                    'currency_id': expense.currency_id.id,
                                    'account_id': expense.customer.property_account_receivable_id.id,
                                    'partner_id': expense.customer.id,
                                    'analytic_account_id': expense.analytic_account_id.id,
                                    'analytic_tag_ids': expense.analytic_tag_ids.id,

                                })]
                            }
                        else:
                            balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                                   expense.company_id, dt)
                            debit = credit = balance
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.code,
                                    'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                }), (0, 0, {
                                    'name': expense.code,
                                    'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.account_id.id,
                                    'partner_id': expense.customer.id,
                                    'analytic_account_id': expense.analytic_account_id.id,
                                    'analytic_tag_ids': expense.analytic_tag_ids.id,

                                })]
                            }
                    elif self.payment_type == 'expense_money':
                        dt = expense.date

                        balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                               expense.company_id, dt)
                        debit = credit = balance
                        if self.customer:
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.description,
                                    'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.customer.property_account_payable_id.id,
                                    'partner_id': expense.customer.id,
                                    'analytic_account_id': expense.analytic_account_id.id,
                                    'analytic_tag_ids': expense.analytic_tag_ids.id,

                                }), (0, 0, {
                                    'name': expense.description,
                                    'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                })]
                            }
                        else:
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.description,
                                    'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.account_id.id,
                                    'partner_id': expense.customer.id,
                                    'analytic_account_id': expense.analytic_account_id.id,
                                    'analytic_tag_ids': expense.analytic_tag_ids.id,

                                }), (0, 0, {
                                    'name': expense.description,
                                    'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                })]
                            }
                    elif self.payment_type == 'transfer_money':
                        dt = expense.date

                        balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                               expense.company_id, dt)
                        debit = credit = balance
                        move = {
                            # 'journal_id': expense.treasury.id,
                            'date': dt,
                            'ref': expense.note,
                            'line_ids': [(0, 0, {
                                'name': expense.description,
                                'credit': debit,
                                'amount_currency': debit,
                                'currency_id': expense.currency_id.id,
                                'account_id': expense.account_to.id,
                                'partner_id': expense.customer.id,
                            }), (0, 0, {
                                'name': expense.description,
                                'debit': credit,
                                'amount_currency': -credit,
                                'currency_id': expense.currency_id.id,
                                'account_id': expense.account_from.id,
                                'analytic_account_id': expense.analytic_account_id.id,
                                'analytic_tag_ids': expense.analytic_tag_ids.id,

                            })]
                        }

                    move_id = self.env['account.move'].create(move)

                    move_id.post()
                    self.write({'state': 'confirm',
                                'code': move_id.name
                                })
                else:
                    if self.payment_type == 'receive_money':
                        dt = expense.date
                        if self.customer:
                            balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                                   expense.company_id, dt)
                            debit = credit = balance
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.code,
                                    'debit': debit, ''
                                                    'amount_currency': debit,
                                    'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                }), (0, 0, {
                                    'name': expense.code,
                                    'credit': credit,
                                    'amount_currency': -credit,
                                    'currency_id': expense.currency_id.id,
                                    'account_id': expense.customer.property_account_receivable_id.id,
                                    'partner_id': expense.customer.id,
                                    'analytic_tag_ids': expense.analytic_tag_ids.id,

                                })]
                            }
                        else:
                            balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                                   expense.company_id, dt)
                            debit = credit = balance
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.code,
                                    'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                }), (0, 0, {
                                    'name': expense.code,
                                    'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.account_id.id,
                                    'partner_id': expense.customer.id,

                                })]
                            }
                    elif self.payment_type == 'expense_money':
                        dt = expense.date

                        balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                               expense.company_id, dt)
                        debit = credit = balance
                        if self.customer:
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.description,
                                    'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.customer.property_account_payable_id.id,
                                    'partner_id': expense.customer.id,
                                }), (0, 0, {
                                    'name': expense.description,
                                    'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                })]
                            }
                        else:
                            move = {
                                'journal_id': expense.treasury.id,
                                'date': dt,
                                'ref': expense.note,
                                'line_ids': [(0, 0, {
                                    'name': expense.description,
                                    'debit': debit, 'amount_currency': debit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.account_id.id,
                                    'partner_id': expense.customer.id,
                                }), (0, 0, {
                                    'name': expense.description,
                                    'credit': credit, 'amount_currency': -credit, 'currency_id': expense.currency_id.id,
                                    'account_id': expense.treasury.default_account_id.id,

                                })]
                            }
                    elif self.payment_type == 'transfer_money':
                        dt = expense.date

                        balance = expense.currency_id._convert(expense.amount, expense.company_currency_id,
                                                               expense.company_id, dt)
                        debit = credit = balance
                        move = {
                            # 'journal_id': expense.treasury.id,
                            'date': dt,
                            'ref': expense.note,
                            'line_ids': [(0, 0, {
                                'name': expense.description,
                                'credit': debit,
                                'amount_currency': debit,
                                'currency_id': expense.currency_id.id,
                                'account_id': expense.account_to.id,
                                'partner_id': expense.customer.id,
                            }), (0, 0, {
                                'name': expense.description,
                                'debit': credit,
                                'amount_currency': -credit,
                                'currency_id': expense.currency_id.id,
                                'account_id': expense.account_from.id,

                            })]
                        }

                    move_id = self.env['account.move'].create(move)

                    move_id.post()
                    self.write({'state': 'confirm',
                                'code': move_id.name
                                })

    def draft(self):
        for record in self:
            res = self.env['account.move'].search([('name', '=', record.code)])
            if res:
                res.button_draft()
                self.write({'state': 'draft'})

    def cancel(self):
        for record in self:
            res = self.env['account.move'].search([('name', '=', record.code)])
            if res:
                res.button_cancel()
                self.write({'state': 'cancel'})
