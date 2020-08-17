# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

################################################################################

class ResCity(models.Model):
    _inherit = 'res.city'

    description = fields.Text(
        "Deskripsi", 
        tracking=True)

    kode_id = fields.Char(
        "No ID")
        
    subdistrict_ids = fields.One2many(
        string="daftar Kecamatan", 
        comodel_name="res.subdistrict", 
        inverse_name="city_id")
    
