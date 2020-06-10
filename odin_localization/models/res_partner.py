# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """ Extend partner"""
    _inherit = 'res.partner'

    kota_id = fields.Many2one(
        'res.partner.kota',
        'Kota',
    )

    kecamatan = fields.Char(
        'Kecamatan',
    )

    kelurahan = fields.Char(
        'Kelurahan',
    )

    alamat_npwp = fields.Char(
        'Alamat NPWP',
    )

    pkp = fields.Boolean(
        'PKP',
        default=False,
    )

    @api.onchange('kota_id')
    def _onchange_kota_id(self):
        self.city = self.kota_id.name
        self.state_id = self.kota_id.state_id


class ResPartnerKota(models.Model):
    """ Define Kota """

    _name = 'res.partner.kota'
    _description = 'Kota'

    name = fields.Char(
        'Kota',
        required=True,
    )

    state_id = fields.Many2one(
        'res.country.state',
        'Provinsi',
        required=True,
        domain="[('res.country','=','Indonesia')]"
    )
