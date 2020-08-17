# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

################################################################################


class ResSubdistrict(models.Model):
    _name = 'res.subdistrict'
    _description = 'Kecamatan'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Nama Kecamatan", required=True, tracking=True)
    description = fields.Text("Deskripsi", tracking=True)
    village_ids = fields.One2many(string="daftar Kelurahan", comodel_name="res.village", inverse_name="subdistrict_id")
    city_id = fields.Many2one('res.city', string='Kota', required=True)
    kode_id = fields.Char(
        "No ID")
    
