from odoo import models, fields, api
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import float_round
from datetime import time
import math

WeakDays = [ 'الاثنين', 'الثلاثاء', 'الاربعاء', 'الخميس', 'الجمعه','السبت', 'الاحد']

def float_to_time(hours):
    """ Convert a number of hours into a time object. """
    if hours == 24.0:
        return time.max
    fractional, integral = math.modf(hours)
    return time(int(integral), int(float_round(60 * fractional, precision_digits=0)))


class FormTimingReport(models.Model):
    _name = 'form.timing.report'
    user_id = fields.Many2one('res.users', 'User', required=1)
    partner_id = fields.Many2one('res.partner', 'Partner', required=1)
    form_id = fields.Many2one('form.design', 'Form', domain="[('type','=', 'timing')]", required=1)
    from_date = fields.Date('From Date', required=1)
    type = fields.Selection([('resident', 'Resident'), ('worker', 'Worker')], string="Type",
                            store=True,
                            tracking=True)
    to_date = fields.Date('To Date', required=1)

    def get_field_row(self):
        dt = datetime.combine(self.to_date, datetime.max.time())
        df = datetime.combine(self.from_date, datetime.min.time())
        forms = self.env['form.apply.line.matrix'].search([('form_line_id.form_id', '=', self.form_id.id),
                                                           ('form_line_id.partner_id', '=', self.partner_id.id),
                                                           ('notify_time','>=', df),
                                                           ('notify_time','<=',dt)])
        list2 = self.env['form.line.answer']
        list2= forms.mapped('matrix_id')
        itemslist = list(dict.fromkeys(list2))
        return itemslist

    def get_day(self,value):
        return WeakDays[value]

    def get_filed_value(self, row, col):
        for record in self:
            dt = datetime.combine(row, datetime.max.time())
            df = datetime.combine(row, datetime.min.time())
            raws = self.env['form.apply.line.matrix'].search([('matrix_id','=', col.id), ('form_line_id.form_id', '=', self.form_id.id),
                                                        ('notify_time','>=', df), ('notify_time','<=',dt)])
            for raw in raws:
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
                    return {'value': raw.date_time.time.strftime('%H:%M'),
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
        return {'value': '',
                'type': ''}

    def get_field_col(self):
        dt = datetime.combine(self.to_date, datetime.max.time())
        df = datetime.combine(self.from_date, datetime.min.time())
        forms = self.env['form.apply.line.matrix'].search([('form_line_id.form_id', '=', self.form_id.id),
                                                           ('form_line_id.partner_id', '=', self.partner_id.id),
                                                           ('notify_time', '>=', df),
                                                           ('notify_time', '<=', dt)])
        itemslist =[]
        list2 =[]
        for record in forms:
             list2.append(record.notify_time.date())
        itemslist = list(dict.fromkeys(list2))
        return itemslist

    def print_pdf(self):
        context = {
            'lang': 'en_US',
            'active_ids': [self.id],
        }
        return {
            'context': context,
            'data': None,
            'type': 'ir.actions.report',
            'report_name': 'form_timing_report.timing_report',
            'report_type': 'qweb-html',
            'report_file': 'form_timing_report.timing_report',
            'name': 'timing Report',
            'flags': {'action_buttons': True},
        }