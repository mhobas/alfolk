from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class RoomsAccommodationsAlfolk(models.Model):
    _name = 'folk.rooms.accommodations'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "room_id"

    category = fields.Many2one('partner.category', 'Partner Category')
    room_id = fields.Many2one("folk.rooms", "Room", tracking=True, domain=[('status', '=', 'available')])

    partner_name = fields.Many2one("res.partner", domain="[('category','=',category)]", string="Partner Name",
                                   tracking=True,
                                   required=True,)
    # partner_code = fields.Char('Partner Code', readonly=True, related='partner_name.name',invisible=True)
    bed_reserve_from = fields.Date("Reservation From", store=True, tracking=True, default=datetime.today())
    bed_reserve_to = fields.Date("Reservation To", store=True, tracking=True, default=datetime.today())
    responsible_id = fields.Many2one('hr.employee', store=True, tracking=True)

    _sql_constraints = [
        ('bed_partner_code_uniq', 'unique(partner_name, bed_reserve_from,bed_reserve_to)',
         'this partner can not reserved another bed in the same period'),

    ]

    @api.model
    def _getbed(self):
        for record in self:
            t = []
            available_bed = self.env['folk.rooms'].search(
                [('id', '=', record.room_id.id)])
            if available_bed:
                for x in available_bed.bed_id:

                    if x.bed_status == "available":
                        t.append(x.id)
                return t
            else:
                return False

    @api.depends('room_id')
    def _load_bed(self):
        for record in self:
            if record.room_id:
                record.bed_ids = record._getbed()
            else:
                record.bed_ids = False

    bed_ids = fields.Many2many('folk.beds', string="beds", store=True, tracking=True, compute='_load_bed')
    bed_id = fields.Many2one('folk.beds', string="Bed", store=True, tracking=True,
                             domain="[('id', 'in',bed_ids)]")

    @api.constrains('bed_reserve_from', 'bed_reserve_to')
    def check_in_out(self):
        for rec in self:
            if rec.bed_reserve_from and rec.bed_reserve_to:
                if rec.bed_reserve_to < rec.bed_reserve_from:
                    raise ValidationError(_("Date Of Reservation From Must Be Before Date Of Reservation TO"))



    # @api.constrains('bed_reserve_from', 'bed_reserve_to', 'bed_id','partner_name')
    # def check_availabilty_bed(self):
    #     for rec in self:
    #         if rec.bed_id and rec.bed_reserve_from and rec.bed_reserve_to and rec.partner_name:
    #             raise ValidationError(_("Sorry you cant not reserve this bed in this period"))

    # @api.constrains('status')
    # def check_availability_bed(self):
    #     for rec in self:
    #         if rec.status == 'occupied':
    #             raise ValidationError(_("Sorry! You Can Not Reserve This bed"))

    # record.description = "Test for partner %s" % record.partner_id.name
