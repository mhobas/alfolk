# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date


class res_partner_category(models.Model):
    _name = 'partner.category'
    _description = 'Partner Category'
    _rec_name = 'name'

    name = fields.Char('Name', store=True)

    category_type = fields.Selection([
        ('resident', 'resident'), ('non', 'Non-resident')], string='Category Type')


class res_partner_edit(models.Model):
    _inherit = 'res.partner'
    category = fields.Many2one('partner.category', "Category", store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], "Gender", store=True)
    father_name = fields.Char('Father Name', store=True)
    mother_name = fields.Char('Mother Name', store=True)
    date_of_birth = fields.Date('Birth Of Date', store=True)
    identification_id = fields.Char('Identification ID', store=True)
    # code = fields.Char('Code', store=True, required=True)
    doctor_name = fields.Many2one('hr.employee', string='Doctor Phone', store=True, )
    doctor_phone = fields.Char('Doctor Phone', store=True, )

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", "=", name), ("name", operator, name)]

        partners = self.search(domain + args, limit=limit)
        return partners.name_get()

    @api.depends('date_of_birth')
    def calculate_age(self):
        for record in self:
            if record.date_of_birth:
                today = date.today()
                record.age = today.year - self.date_of_birth.year - (
                        (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            else:
                return False

    # @api.depends('date_of_birth')
    # def compute_age(self):
    #     for record in self:
    #         if record.date_of_birth:
    #             rdelta = relativedelta(date.today(), record.date_of_birth)
    #             record.age = rdelta
    #         else:
    #             record.age = False

    age = fields.Char('Age', store=True, compute='calculate_age')


class sales_order(models.Model):
    _inherit = 'sale.order'
    category = fields.Many2one('partner.category', "Category", store=True)

    @api.onchange('category')
    def _onchange_cust_categ_id(self):
        self.partner_id = False
        return {'domain': {'person': [('partner_id', '=', self.category.id)]}}
