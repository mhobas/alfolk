from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class ResPartnerInherited(models.Model):
    _inherit = 'res.partner'
    code = fields.Char('Code', store=True, tracking=True, index=True, default='', readonly=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'Code of partner must be unique'),

    ]
    new_image = fields.Image("Other Image", store=True, compute_sudo=True)

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", "=", name), ("name", operator, name)]

        partners = self.search(domain + args, limit=limit)
        return partners.name_get()

    @api.depends('name', 'code')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.code:
                name = record.code + ' / ' + name
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        if vals.get('code', _('')) == _(''):
            vals['code'] = self.env['ir.sequence'].next_by_code('res.partner') or _('')
        print("success")
        res = super(ResPartnerInherited, self).create(vals)
        return res
