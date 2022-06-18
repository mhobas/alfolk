from odoo import models, fields, api, _
from odoo.exceptions import UserError
from calendar import monthrange


class Partner(models.Model):
    _inherit = 'res.partner'

    def open_medical_form(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'medical'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'medical'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'medical'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def view_closed_forms(self):
        for record in self:
            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('partner_id', '=', record.id), ('state', '=', 'done')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_physical_measurements(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'physical'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'physical'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'physical'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_nutrition(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'nutrition'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'nutrition'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'nutrition'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_timing(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'timing'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'timing'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'timing'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_achievement_rate(self):
        for record in self:
            record.show_achievement = True

    def open_achievement_worker(self):
        for record in self:
            record.show_achievement = False
            record.show_resident = False
            exist = record.env['form.apply'].search([('form_type', '=', 'achievement'), ('form_id.assign_type', '=', 'worker'),
                                                     ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'achievement'), ('assign_type', '=', 'worker'), '|', ('category', '=', record.category.id),
                     ('category', '=', False)])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'achievement'),
                           ('partner_id', '=', record.id),
                           ('form_id.assign_type', '=', 'worker'),
                           ('state', '=', 'draft'),
                           ('type', '=', 'worker')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_achievement_other(self):
        for record in self:
            record.show_achievement = False
            record.show_resident = False
            exist = record.env['form.apply'].search([('form_type', '=', 'achievement'),('form_id.assign_type', '=', 'other'),
                                                     ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'achievement'),
                     ('assign_type', '=', 'other'), '|',
                     ('category', '=', record.category.id),
                     ('category', '=', False)])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'achievement'),
                           ('partner_id', '=', record.id),
                           ('form_id.assign_type', '=', 'other'),
                           ('state', '=', 'draft'),
                           ],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_achievement_resident(self):
        for record in self:
            record.show_resident = True

    def open_achievement_morning(self):
        for record in self:
            ids = []
            record.show_resident = False
            record.show_achievement = False

            exist = record.env['form.apply'].search([('form_type', '=', 'achievement'),
                                                     ('type', '=', 'resident'), ('task_type', '=', 'morning'),
                                                     ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'achievement'), '|', ('category', '=', record.category.id),
                     ('category', '=', False),('task_type', '=', 'morning'), ('assign_type', '=', 'resident')])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'achievement'), ('partner_id', '=', record.id),
                           ('state', '=', 'draft'),
                           ('type', '=', 'resident'), ('task_type', '=', 'morning'),],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_achievement_night(self):
        for record in self:
            ids = []
            record.show_resident = False
            record.show_achievement = False

            exist = record.env['form.apply'].search([('form_type', '=', 'achievement'),
                                                     ('type', '=', 'resident'), ('task_type', '=', 'night'),
                                                     ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'achievement'), '|', ('category', '=', record.category.id),
                     ('category', '=', False),('task_type', '=', 'night'), ('assign_type', '=', 'resident')])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'achievement'), ('partner_id', '=', record.id),
                           ('state', '=', 'draft'),
                           ('type', '=', 'resident'), ('task_type', '=', 'night'),],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_achievement_periodic(self):
        for record in self:
            record.show_resident = False
            record.show_achievement = False
            exist = record.env['form.apply'].search([('form_type', '=', 'achievement'),
                                                     ('type', '=', 'resident'), ('task_type', '=', 'periodic'),
                                                     ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'achievement'), '|', ('category', '=', record.category.id),
                     ('category', '=', False),('task_type', '=', 'periodic'), ('assign_type', '=', 'resident')])
                for form in forms:
                    lines = []
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
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'achievement'), ('partner_id', '=', record.id),
                           ('state', '=', 'draft'),
                           ('type', '=', 'resident'), ('task_type', '=', 'periodic')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    is_student = fields.Boolean(compute='_compute_is_student', store=False)
    show_achievement = fields.Boolean('Achievement', store=True)
    show_resident = fields.Boolean('Resident', store=True)

    @api.onchange('category')
    def _compute_is_student(self):
        for record in self:
            if record.category.category_type:
                record.is_student = True
            else:
                record.is_student = False
