# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

################################################################################


class ResVillage(models.Model):
    _name = 'res.village'
    _description = 'Kelurahan'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Nama Kelurahan", required=True, tracking=True)
    zipcode = fields.Char("Kodepos", tracking=True)
    description = fields.Text("Deskripsi", tracking=True)
    subdistrict_id = fields.Many2one('res.subdistrict', string='Kecamatan', required=True)
