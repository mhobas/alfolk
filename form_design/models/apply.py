import math
from datetime import time

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from calendar import monthrange
from datetime import datetime, timedelta
from odoo.tools import float_round
from dateutil.relativedelta import relativedelta

from pytz import timezone, UTC

WeakDays = ['السبت', 'الاحد', 'الاثنين', 'الثلاثاء', 'الاربعاء', 'الخميس', 'الجمعه']


def float_to_time(hours):
    """ Convert a number of hours into a time object. """
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    return time(int(integral), int(float_round(60 * fractional, precision_digits=0)))


class ApplyFormDesign(models.Model):
    _name = 'form.apply'
    _description = 'Form Apply'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'complete_name'
    _sql_constraints = [
        ('form_partner_day_uniq', 'unique(form_id, partner_id, date)',
         'This form already exist'),

    ]
    category = fields.Many2one('partner.category', 'Partner Category', store=True, index=True, tracking=True,
                               related='form_id.category', readonly=1)
    task_type = fields.Selection(store=True, index=True, tracking=True,
                                 related='form_id.task_type', readonly=1)

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_('Closed Form Cannot be deleted'))
        res = super(ApplyFormDesign, self).unlink()
        return res

    form_id = fields.Many2one('form.design', 'Form', store=True, index=True, tracking=True)
    partner_id = fields.Many2one('res.partner', 'Partner', domain="[('category','=',category)]", store=True, index=True,
                                 tracking=True, required=1)
    apply_ids = fields.One2many('form.apply.line', 'apply_id', store=True, index=True, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Closed')], default='draft', store=True,
                             tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True, store=True, index=True, required=1)
    end_date = fields.Datetime('End Date', store=True)
    complete_name = fields.Char('Name', compute='_compute_name', store=True, index=True, tracking=True)
    allow_add = fields.Boolean("Allow Add Line", compute="compute_allow_add_line")
    is_decline = fields.Boolean("Declined Form", store=True)
    type = fields.Selection([('resident', 'Resident'), ('worker', 'Worker')], string="Type",
                            store=True,
                            tracking=True, related='form_id.assign_type')
    form_type = fields.Selection(related='form_id.type', store=True)

    def view_form_fill_in_line(self):
        return {
            'name': _('Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'form.apply.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.apply_ids.ids)],
            'context': self.env.context,
        }

    @api.depends('date', 'partner_id')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.partner_id:
                name += ' ' + record.partner_id.name
            if record.form_id:
                name += ' ' + record.form_id.name
            if record.date:
                name += ' ' + str(record.date)
            record.complete_name = name

    def set_close(self):
        self.state = 'done'
        close_date = datetime.fromisoformat(self.date.isoformat())
        for line in self.apply_ids:
            for answer in line.answers_ids.filtered(lambda a: a.type == 'time'):
                if answer.time > 0.0:
                    if answer.val_name in WeakDays:

                        index = WeakDays.index(answer.val_name)
                        answer.notify_time = datetime.combine(self.date, float_to_time(answer.time)) + relativedelta(
                            days=index) - relativedelta(hours=2)
                        if answer.notify_time > close_date:
                            close_date = answer.notify_time

                    if answer.val_name.isnumeric():
                        answer.notify_time = datetime.combine(self.date, float_to_time(answer.time)) + relativedelta(
                            days=int(answer.val_name) - 1) - relativedelta(hours=2)
                        if answer.notify_time > close_date:
                            close_date = answer.notify_time
                elif answer.date_time:
                    answer.notify_time = answer.date_time
                    if answer.notify_time > close_date:
                        close_date = answer.notify_time
                self.end_date = close_date
        for record in self.search([('partner_id', '=', self.partner_id.id), ('form_id', '=', self.form_id.id),
                                   ('end_date', '<', self.end_date), ('end_date', '>', datetime.now())]):
            record.is_decline = True

    def set_new(self):
        self.state = 'draft'

    @api.onchange('form_id')
    def form_change(self):
        for record in self:
            record.apply_ids = False
            forms = record.form_id
            lines = []
            if record.state == 'draft' and not record.apply_ids and record.form_id:
                for form in forms:
                    for line in form.question_ids:
                        lines.append((0, 0, {
                            'name': line.title,
                            'sequence': line.sequence,
                            'form_line_id': line._origin.id,
                            'user_id': line.user_id.id,
                            'form_id': form._origin.id,
                            'question_type': line.question_type,
                            'matrix_answer_type': line.matrix_answer_type,
                        }))
                self.write({'apply_ids': lines})

    @api.onchange("form_id")
    def compute_allow_add_line(self):
        for record in self:
            if record.form_id:
                record.allow_add = record.form_id.allow_add
            else:
                record.allow_add = False

    def action_done(self):
        self.state = 'done'

    def confirm(self):
        lines = self.apply_ids.filtered(lambda line: (not line.answer or line.question_type == 'matrix') and (
                line.user_id == self.env.user or not line.user_id))
        if lines:
            return {
                'name': _('Answers'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply.line',
                'view_mode': 'form',
                'view_id': self.env.ref('form_design.form_apply_line_form_view2').id,
                'res_id': lines[0].id,
                'target': 'new',
                'domain': [('id', '=',
                            self.apply_ids.filtered(lambda line: not line.answer or line.question_type == 'matrix')[
                                0].id)],
                'context': self.env.context,
            }

    def add_line(self):
        if self.form_id.question_ids:
            return {
                'name': _('Answers'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply.line',
                'view_mode': 'form',
                'view_id': self.env.ref('form_design.form_apply_line_form_view').id,
                'target': 'new',
                'context': {
                    'default_form_id': self.form_id.id,
                    'default_apply_id': self._origin.id,
                    'default_form_line_id': self.form_id.question_ids[0].id
                },
            }


class FormApplyLine(models.Model):
    _name = 'form.apply.line'
    _description = 'Form Apply Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id'

    @api.model
    def get_notifiction(self):
        date = fields.Datetime.now()
        notifications = self.search([('form_id.type', '=', 'timing'), ('state', '=', 'done'), ('date_time', '>=', date),
                                     ('date_time', '<=', date + relativedelta(days=1)),
                                     ('apply_id.state', '=', 'done'), ('apply_id.is_decline', '=', False), ])
        notification = self.answers_ids.search(
            [('apply_id.form_id.type', '=', 'timing'), ('apply_id.state', '=', 'done'),
             ('notify_time', '<=', date + relativedelta(days=1)),
             ('notify_time', '>=', date), ('apply_id.is_decline', '=', False)])
        print(date + relativedelta(days=1))
        print(date)
        for n in notifications:
            n.form_line_id.message_post(
                partner_ids=[a.partner_id.id for a in n.notify_ids],
                subject='',
                body='Kindly See your schedule for partner ' + str(n.form_line_id.partner_id.name) + ' ' +
                     str(n.form_line_id.form_id.name + ' ' + str(n.notify_time)),
                subtype_id=self.env.ref('mail.mt_comment').id,
                email_layout_xmlid='mail.mail_notification_light',
            )
        for n in notification:
            n.form_line_id.message_post(
                partner_ids=[a.partner_id.id for a in n.form_line_id.notify_ids],
                subject='',
                body='Kindly See your schedule for ' + str(n.form_line_id.partner_id.name) + ' ' +
                     str(n.form_line_id.form_id.name + ' ' + str(n.notify_time)),
                subtype_id=self.env.ref('mail.mt_comment').id,
                email_layout_xmlid='mail.mail_notification_light',
            )

    def get_field_col(self):
        for record in self:
            itemslist = record.answers_ids.mapped('val_name')
            itemslist = list(dict.fromkeys(itemslist))
            return itemslist

    def get_field_row(self):
        for record in self:
            itemslist = record.answers_ids.mapped('matrix_id')
            itemslist = list(dict.fromkeys(itemslist))
            return itemslist

    def get_filed_value(self, col, row):
        for record in self:
            raw = record.answers_ids.filtered(lambda line: line.val_name == col and line.matrix_id == row)
            if raw.is_header:
                return {'value': '',
                        'type': raw.type}
            elif raw.type == 'boolean':
                return {'value': raw.check,
                        'type': raw.type}
            elif raw.type == 'text':
                return {'value': raw.text,
                        'type': raw.type}
            elif raw.type == 'date':
                return {'value': raw.date,
                        'type': raw.type}
            elif raw.type == 'datetime':
                return {'value': raw.date_time,
                        'type': raw.type}
            elif raw.type == 'char':
                return {'value': raw.textChar,
                        'type': raw.type}
            elif raw.type == 'time':
                return {'value': float_to_time(raw.time).strftime('%H:%M'),
                        'type': raw.type}
            elif raw.type == 'numerical_box':
                return {'value': raw.value,
                        'type': raw.type}
            elif raw.type == 'simple_choice':
                return {'value': raw.value_id.name,
                        'type': raw.type}
            elif raw.type == 'multiple_choice':
                return {'value': ' , '.join(raw.value_ids.mapped('name')),
                        'type': raw.type}

    def save_and_close(self):
        return {'type': 'ir.actions.act_window_close'}

    def _compute_can_edit(self):
        for record in self:
            if not record.user_id and record.state == 'draft':
                record.can_edit = True
            elif record.user_id == record.env.user and record.state == 'draft':
                record.can_edit = True
            else:
                record.can_edit = False

    def compute_has_next(self):
        for record in self:
            has_next = False
            if record.apply_id.apply_ids:
                ids = record.apply_id.apply_ids.mapped('id')
                ids.sort()
                if record._origin.id in ids:
                    next_index = ids.index(record._origin.id) + 1
                    if next_index < len(ids):
                        has_next = True
            record.has_next = has_next

    has_next = fields.Boolean(compute='compute_has_next')
    can_edit = fields.Boolean(compute="_compute_can_edit")

    @api.onchange('form_line_id')
    def _onchange_form_line(self):
        for record in self:
            if record.form_line_id:
                record.name = record.form_line_id.title
                record.question_type = record.form_line_id.question_type

    @api.constrains('form_line_id')
    def constraint_form_line(self):
        for record in self:
            if record.form_line_id:
                record.name = record.form_line_id.title
                record.question_type = record.form_line_id.question_type

    @api.constrains('form_line_id')
    def compute_answer_lines(self):
        for record in self:
            answers = record.answers_ids
            if not record.answers_ids and record.form_line_id:
                line = record.form_line_id
                if line.question_type == 'matrix':
                    for m in line.suggested_answer_ids:
                        if line.matrix_answer_ids:
                            for c in line.matrix_answer_ids:
                                if line.matrix_answer_type == 'multi':
                                    answers += record.answers_ids.create({
                                        'name': m.value,
                                        'val_name': c.value,
                                        'apply_id': record.apply_id.id,
                                        'is_required': m.is_required,
                                        'is_header': m.is_header,
                                        'type': c.type,
                                        'matrix_id': m._origin.id,
                                        'col_id': c._origin.id,

                                    })
                                else:
                                    answers += record.answers_ids.create({
                                        'name': m.value,
                                        'val_name': c.value,
                                        'apply_id': record.apply_id._origin.id,
                                        'col_id': c._origin.id,
                                        'is_required': m.is_required,
                                        'is_header': m.is_header,
                                        'type': line.matrix_answer_type,
                                        'matrix_id': m._origin.id,

                                    })
                        elif line.matrix_coltype == 'month':
                            num_days = monthrange(fields.date.today().year, fields.date.today().month)[1]
                            for c in range(1, num_days + 1):
                                answers += record.answers_ids.create({
                                    'name': m.value,
                                    'val_name': c,
                                    'apply_id': record.apply_id._origin.id,
                                    'is_required': m.is_required,
                                    'type': record.matrix_answer_type,
                                    'matrix_id': m._origin.id,

                                })
                        elif line.matrix_coltype == 'week':
                            for c in range(0, 7):
                                answers += record.answers_ids.create({
                                    'name': m.value,
                                    'val_name': WeakDays[c],
                                    'apply_id': record.apply_id._origin.id,
                                    'is_required': m.is_required,
                                    'type': record.matrix_answer_type,
                                    'matrix_id': m._origin.id,

                                })
            record.answers_ids = answers

    user_id = fields.Many2one('res.users', string='Responsible', tracking=True, store=True)
    state = fields.Selection(related='apply_id.state', store=True)
    sequence = fields.Integer('Label Sequence order', default=10)
    name = fields.Char('Title', store=True, index=True)
    answer = fields.Char('Answer', compute='compute_answer')
    note = fields.Char('Note', store=True, index=True)
    text_char = fields.Char('Answer', store=True, index=True)
    text = fields.Text('Answer', store=True, index=True)
    numerical_box = fields.Float('Numerical', store=True, index=True)
    date = fields.Date('Date', store=True)
    check = fields.Boolean('Check', store=True, index=True)
    date_time = fields.Datetime('Date Time', store=True, index=True)
    form_line_id = fields.Many2one('form.design.line', 'Question', domain="[('form_id','=',form_id)]", store=True,
                                   index=True)
    form_id = fields.Many2one('form.design', 'Form', store=True, index=True)
    apply_id = fields.Many2one('form.apply', ondelete='cascade', index=True, store=True)
    partner_id = fields.Many2one(related='apply_id.partner_id', store=True)
    employee_id = fields.Many2one('hr.employee', 'Responsible Employee', store=True)
    notify_ids = fields.Many2many('res.users', string='Notification To', store=True)
    suggested_id = fields.Many2one('form.line.value', 'Suggested Answer', domain="[('question_id','=',form_line_id)]",
                                   store=True)
    suggested_ids = fields.Many2many('form.line.answer', string='Suggested Answer',
                                     domain="[('question_id','=',form_line_id)]")
    answers_ids = fields.One2many('form.apply.line.matrix', 'form_line_id', string='Matrix Answer', store=True)

    question_type = fields.Selection([
        ('text_box', 'Multiple Lines Text Box'),
        ('char_box', 'Single Line Text Box'),
        ('numerical_box', 'Numerical Value'),
        ('check', 'True or False'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('multiple_choice', 'Multiple choice: multiple answers allowed'),
        ('matrix', 'Matrix')], string='Question Type',
        readonly=False, store=True)
    matrix_answer_type = fields.Selection([('date', 'Date'),
                                           ('time', 'Time'),
                                           ('datetime', 'DateTime'),
                                           ('boolean', 'CheckBox'),
                                           ('numerical_box', 'Numerical Value'),
                                           ('char', 'Single Line Text Box'),
                                           ('simple_choice', 'Multiple choice: only one answer'),
                                           ('text', 'Multiple Lines Text Box'),
                                           ('multi', 'Multiple Types')], string='Matrix Answer Type',
                                          default='boolean', store=True)

    def confirm(self):
        ids = self.apply_id.apply_ids.filtered(lambda line: (not line.answer or line.question_type == 'matrix') and (
                line.user_id == self.env.user or not line.user_id)).mapped('id')
        ids.sort()
        if self._origin.id in ids:
            next_index = ids.index(self._origin.id) + 1
            if next_index < len(ids):
                return {
                    'name': _('Answers'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'form.apply.line',
                    'view_mode': 'form',
                    'view_id': self.env.ref('form_design.form_apply_line_form_view2').id,
                    'res_id': ids[next_index],
                    'target': 'new',
                    'context': self.env.context,
                }

    def confirm_view(self):
        ids = self.apply_id.apply_ids.filtered(lambda line: (not line.answer or line.question_type == 'matrix') and (
                line.user_id == self.env.user or not line.user_id)).mapped('id')
        ids.sort()
        if self._origin.id in ids:
            next_index = ids.index(self._origin.id) + 1
            if next_index < len(ids):
                return {
                    'name': _('Answers'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'form.apply.line',
                    'view_mode': 'form',
                    'view_id': self.env.ref('form_design.form_apply_line_form_view').id,
                    'res_id': ids[next_index],
                    'target': 'current',
                    'context': self.env.context,
                }

    @api.onchange('text_char', 'text', 'check', 'numerical_box', 'date', 'date_time', 'suggested_id' 'suggested_ids',
                  'answers_ids')
    def compute_answer(self):
        for record in self:
            if record.question_type == 'char_box' and record.text_char:
                record.answer = record.text_char
            elif record.question_type == 'text_box' and record.text:
                record.answer = record.text
            elif record.question_type == 'check':
                record.answer = str(record.check)
            elif record.question_type == 'numerical_box' and record.numerical_box:
                record.answer = str(record.numerical_box)
            elif record.question_type == 'date' and record.date:
                record.answer = str(record.date)
            elif record.question_type == 'datetime' and record.date_time:
                record.answer = str(record.date_time)
            elif record.question_type == 'simple_choice' and record.suggested_id:
                record.answer = str(record.suggested_id.value)
            elif record.question_type == 'multiple_choice' and record.suggested_ids:
                record.answer = ','.join([r.value for r in record.suggested_ids])
            elif record.question_type == 'matrix' and record.answers_ids:
                if record.matrix_answer_type == 'boolean':
                    record.answer = ','.join(
                        [r.name + ' ' + r.val_name for r in record.answers_ids.filtered(lambda x: x.check)])
                elif record.matrix_answer_type == 'text':
                    record.answer = ','.join(
                        [r.name + ' ' + r.val_name for r in record.answers_ids.filtered(lambda x: x.text)])
                elif record.matrix_answer_type == 'date':
                    record.answer = ','.join(
                        [r.name + ' ' + r.val_name for r in record.answers_ids.filtered(lambda x: x.date)])
                elif record.matrix_answer_type == 'datetime':
                    record.answer = ','.join(
                        [r.name + ' ' + r.val_name for r in record.answers_ids.filtered(lambda x: x.date_time)])
                elif record.matrix_answer_type == 'char':
                    record.answer = ','.join(
                        [r.name + ' ' + r.val_name for r in record.answers_ids.filtered(lambda x: x.textChar)])
                elif record.matrix_answer_type == 'time':
                    record.answer = ','.join(
                        [r.name + ' ' + r.val_name for r in record.answers_ids.filtered(lambda x: x.time)])
                else:
                    record.answer = False
            else:
                record.answer = False

    # def write(self, vals):
    #     if self.answers_ids.filtered(lambda answer:answer.is_required):
    #
    #     return super(FormApplyLine, self).write(vals)


class FormApplyLineMatrix(models.Model):
    _name = 'form.apply.line.matrix'
    _description = 'Form Apply Line Matrix'
    matrix_id = fields.Many2one('form.line.answer', store=True, index=True)
    col_id = fields.Many2one('form.line.answer', 'Col', store=True, index=True)
    check = fields.Boolean('Check', store=True, index=True)
    value = fields.Float('Answer Value', store=True, index=True)
    time = fields.Float('Answer Time', store=True, index=True)
    textChar = fields.Char('Answer Char', store=True, index=True)
    date = fields.Date('Answer Date', store=True, index=True)
    date_time = fields.Datetime('Answer DateTime', store=True, index=True)
    text = fields.Text('Answer Text', store=True, index=True)
    name = fields.Char('Row', store=True, index=True)
    val_name = fields.Char('Col', store=True, translate=True, index=True)
    form_line_id = fields.Many2one('form.apply.line', 'Form Fill Out', ondelete='cascade', index=True)
    apply_id = fields.Many2one('form.apply', 'Form Fill Out', store=True, index=True)
    notify_time = fields.Datetime('Notify Time', store=True, index=True)
    is_required = fields.Boolean('Is Required', store=True, index=True)
    is_header = fields.Boolean('Is Header', store=True, index=True)
    type = fields.Selection([('date', 'Date'),
                             ('time', 'Time'),
                             ('datetime', 'DateTime'),
                             ('boolean', 'CheckBox'),
                             ('simple_choice', 'Multiple choice: only one answer'),
                             ('multiple_choice', 'Multiple choice: multiple answers allowed'),
                             ('numerical_box', 'Numerical Value'),
                             ('char', 'Single Line Text Box'),
                             ('text', 'Multiple Lines Text Box')], string='Matrix Answer Type',
                            default='boolean', store=True)
    value_id = fields.Many2one('form.line.value', 'Answer', store=True)
    value_ids = fields.Many2many('form.line.value', string='Answer Many', store=True)
