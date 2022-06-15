from odoo import models, fields, _

WeakDays = ['السبت', 'الاحد', 'الاثنين', 'الثلاثاء', 'الاربعاء', 'الخميس', 'الجمعه']


class FormDesign(models.Model):
    _name = 'form.design'
    _description = 'Form Design'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def compute_form_fill_in(self):
        for record in self:
            record.fill_count = len(record.form_ids)

    type = fields.Selection([('medical', 'Medical File'),
                             ('physical', 'Physical Measurements'),
                             ('nutrition', 'Therapeutic Nutrition'),
                             ('achievement', 'Achievement Rate'),
                             ('timing', 'Timing Form')
                             ], string='Form Type', store=True, index=True, tracking=True)
    assign_type = fields.Selection([('resident', 'Resident'), ('worker', 'Worker'), ('other', 'Other')], string="Assign To",
                                   store=True,
                                   tracking=True)
    task_type = fields.Selection(
        [('morning', 'Morning tasks'), ('night', 'Night tasks'), ('periodic', 'Periodic tasks')], string="Tasks",
        store=True,
        tracking=True)
    category = fields.Many2one('partner.category', 'Partner Category', store=True)
    name = fields.Char('Form Title', required=True, translate=True, tracking=True, store=True, index=True, )
    color = fields.Integer('Color Index', default=0)
    fill_count = fields.Integer('Form Fill In count', default=0, compute='compute_form_fill_in')
    form_ids = fields.Many2many('form.apply', compute='compute_form_ids', string='Form Fill In')

    def compute_form_ids(self):
        for record in self:
            record.form_ids = record.form_ids.search([('form_id', '=', record.ids)])

    description = fields.Html(
        "Description", sanitize=False, translate=True, tracking=True, store=True, index=True, )
    description_done = fields.Html(
        "End Message", translate=True,
        help="This message will be displayed when survey is completed")
    active = fields.Boolean("Active", default=True)
    allow_add = fields.Boolean("Allow Add Line", default=False)
    res_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True,
                             store=True, index=True)
    question_ids = fields.One2many('form.design.line', 'form_id', tracking=True, store=True, index=True, translate=True)

    def view_form_fill_in(self):
        return {
            'name': _(f'Filled out forms of {self.name}'),
            'type': 'ir.actions.act_window',
            'res_model': 'form.apply',
            'view_mode': 'tree,form',
            'domain': [('form_id', '=', self._origin.id)],
            'context': "{'default_form_id': " + str(self._origin.id) + "}",
        }

    def view_form_fill_out_line(self):
        id = self.env.context.get('apply_id')
        if id:
            return {
                'name': _(f'Filled out forms of {self.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply.line',
                'view_mode': 'tree,form',
                'domain': [('apply_id', '=', id), ('form_id', '=', self._origin.id)],
                # 'context': "{'default_form_id': " + str(self._origin.id) + "}",
            }

    def form_fill_in(self):
        lines = []
        for line in self.question_ids:
            lines.append((0, 0, {
                'name': line.title,
                'sequence': line.sequence,
                'form_line_id': line.id,
                'form_id': self._origin.id,
                'question_type': line.question_type,
                'matrix_answer_type': line.matrix_answer_type,
            }))
        return {
            'name': _('Form Fill Out'),
            'type': 'ir.actions.act_window',
            'res_model': 'form.apply',
            'view_mode': 'form',
            'view_id': self.env.ref('form_design.form_apply_form_view').id,
            'target': 'new',
            'context': {
                'default_form_id': self._origin.id,
                'default_apply_ids': lines,
            },
        }


class FormDesignLine(models.Model):
    _name = 'form.design.line'
    _description = 'Form Design Line'
    _rec_name = "title"
    title = fields.Char('Title', required=True, translate=True, tracking=True, store=True, index=True)
    description = fields.Html(
        'Description', translate=True, sanitize=False,
        help="Use this field to add additional explanations about your " +
             "question or to illustrate it with pictures or a video")

    form_id = fields.Many2one('form.design', string='Form', ondelete='cascade', tracking=True, store=True, index=True)
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True, store=True)
    sequence = fields.Integer('Sequence', default=10, tracking=True, store=True, index=True)
    question_type = fields.Selection([
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('check', 'CheckBox'),
        ('numerical_box', 'Numerical Value'),
        ('text_box', 'Multiple Lines Text Box'),
        ('char_box', 'Single Line Text Box'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('multiple_choice', 'Multiple choice: multiple answers allowed'),
        ('matrix', 'Matrix')], string='Question Type',
        readonly=False, store=True, tracking=True, index=True)
    matrix_subtype = fields.Selection([
        ('simple', 'One choice per row'),
        ('multiple', 'Multiple choices per row')], string='Matrix Type', default='simple')

    suggested_answer_ids = fields.One2many('form.line.answer', 'question_id', 'Answers')
    value_answer_ids = fields.One2many('form.line.value', 'question_id', 'Answers')
    matrix_answer_type = fields.Selection([('date', 'Date'),
                                           ('time', 'Time'),
                                           ('datetime', 'DateTime'),
                                           ('boolean', 'CheckBox'),
                                           ('numerical_box', 'Numerical Value'),
                                           ('char', 'Single Line Text Box'),
                                           ('simple_choice', 'Multiple choice: only one answer'),
                                           ('multiple_choice', 'Multiple choice: multiple answers allowed'),
                                           ('text', 'Multiple Lines Text Box'),
                                           ('multi', 'Multiple Types')], string='Matrix Answer Type',
                                          default='boolean', store=True)
    matrix_answer_ids = fields.One2many('form.line.answer', 'matrix_question_id', 'Answers', copy=True)
    matrix_coltype = fields.Selection([
        ('custom', 'Custom'),
        ('week', 'Days of the Week'),
        ('month', 'Days of the Month'),

    ], string='Matrix Columns', default='custom')


class SurveyQuestionAnswer(models.Model):
    _name = 'form.line.answer'
    _description = 'Answers'
    _rec_name = "value"
    _order = 'sequence'
    question_id = fields.Many2one('form.design.line', string='Question', ondelete='cascade')
    matrix_question_id = fields.Many2one('form.design.line', string='Question (as matrix row)', ondelete='cascade')
    sequence = fields.Integer('Label Sequence order', default=10)
    value = fields.Char('Suggested value', translate=True, required=True)
    type = fields.Selection([('date', 'Date'),
                             ('time', 'Time'),
                             ('datetime', 'DateTime'),
                             ('boolean', 'CheckBox'),
                             ('simple_choice', 'Multiple choice: only one answer'),
                             ('numerical_box', 'Numerical Value'),
                             ('char', 'Single Line Text Box'),
                             ('multiple_choice', 'Multiple choice: multiple answers allowed'),
                             ('text', 'Multiple Lines Text Box')], string='Matrix Answer Type',
                            default='boolean', store=True)
    is_correct = fields.Boolean('Is a correct answer')
    is_required = fields.Boolean('Is a Required')
    is_header = fields.Boolean('Is a Header')
    value_ids = fields.One2many('form.line.value', 'matrix_line_id', 'Answers')


class SurveyQuestionAnswerValue(models.Model):
    _name = 'form.line.value'
    _description = 'Answers Values'
    _rec_name = "name"
    _order = 'sequence'
    question_id = fields.Many2one('form.design.line', string='Question', ondelete='cascade')
    matrix_line_id = fields.Many2one('form.line.answer', string='Matrix Line', ondelete='cascade')
    sequence = fields.Integer('Label Sequence order', default=10)
    name = fields.Char('Selection value', translate=True, required=True)
