# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResState(models.Model):
    _inherit = 'res.country.state'

    description = fields.Text(
        "Deskripsi", 
        tracking=True)

    name = fields.Char(
        "Nama Kota", 
        required=True, 
        tracking=True)

    city_ids = fields.One2many(
        string="Cities", 
        comodel_name="res.city", 
        inverse_name="state_id")

    kode_id = fields.Char(
        "No ID")

    code = fields.Char(required=False)