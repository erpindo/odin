from odoo import fields, models, api

class Users(models.Model):
    _inherit = "res.partner"

    timepicker = fields.Char()