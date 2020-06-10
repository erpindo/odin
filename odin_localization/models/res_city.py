# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

################################################################################


class ResCity(models.Model):
    _name = 'res.city'
    _description = 'Kota'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        "Nama Kota", 
        required=True, 
        tracking=True)

    description = fields.Text(
        "Deskripsi", 
        tracking=True)

    subdistrict_ids = fields.One2many(
        string="daftar Kecamatan", 
        comodel_name="res.subdistrict", 
        inverse_name="city_id")

    state_id = fields.Many2one(
        'res.state', 
        'State')
    
