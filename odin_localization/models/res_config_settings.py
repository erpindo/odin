# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.http import Response

import logging
import requests
import json

_logger = logging.getLogger(__name__)

################################################################################

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def action_get_geo_data(self):
        url = "https://dev.farizdotid.com/api/daerahindonesia/"
        r = requests.get("{}provinsi".format(url))
        response = r.json()

        data_prov = response.get('provinsi')
        data_len = len(data_prov)

        country_id = self.env['res.country'].search([('name','ilike','Indonesia')]).ensure_one().id
        print("country_id : {}".format(country_id))

        print("data_len : {}".format(data_len))
        if data_len > 0:
            self.env['res.country.state'].search([('country_id','=',country_id)]).unlink()
            self.env['res.city'].search([('country_id','=',country_id)]).unlink()
            self.env['res.subdistrict'].search([]).unlink()
            self.env['res.village'].search([]).unlink()

        for i in data_prov:
            vals = {
                'kode_id': str(i.get('id')),
                'name': i.get('nama'),
                'country_id': country_id,
            }

            print("i prov : {}".format(i))
            print("vals prov : {}".format(vals))
            prov_id = self.env['res.country.state'].sudo().create(vals)
            
            print("prov_id : {}".format(prov_id))
            print("prov_id.id : {}".format(prov_id.id))
            r = requests.get("{}kota?id_provinsi={}".format(url,i.get('id')))
            response = r.json()

            data_kota = response.get('kota_kabupaten')
            kota_ids = []

            for j in data_kota:
                vals2 = {
                'kode_id': str(j.get('id')),
                'name': j.get('nama'),
                'country_id': country_id,
                'state_id': prov_id.id
                }

                print("j kota : {}".format(j))
                print("vals kota : {}".format(vals2))
                kota_id = self.env['res.city'].sudo().create(vals2)
                kota_ids.append(kota_id.id)

                print("kota_id : {}".format(kota_id))
                print("kota_id.id : {}".format(kota_id.id))

                r2 = requests.get("{}kecamatan?id_kota={}".format(url,j.get('id')))
                response2 = r2.json()

                data_kecamatan = response2.get('kecamatan')
                kecamatan_ids = []

                for k in data_kecamatan:
                    vals3 = {
                    'kode_id': str(k.get('id')),
                    'name': k.get('nama'),
                    'city_id': kota_id.id
                    }

                    print("k kecamatan : {}".format(k))
                    print("vals kecamatan : {}".format(vals3))
                    kecamatan_id = self.env['res.subdistrict'].sudo().create(vals3)
                    kecamatan_ids.append(kecamatan_id.id)

                    print("kecamatan_id : {}".format(kecamatan_id))
                    print("kecamatan_id.id : {}".format(kecamatan_id.id))
                    r3 = requests.get("{}kelurahan?id_kecamatan={}".format(url,k.get('id')))
                    response3 = r3.json()

                    data_kelurahan = response3.get('kelurahan')
                    kelurahan_ids = []

                    for l in data_kelurahan:
                        vals4 = {
                        'kode_id': str(l.get('id')),
                        'name': l.get('nama'),
                        'subdistrict_id': kecamatan_id.id
                        }

                        print("l kelurahan : {}".format(l))
                        print("vals kelurahan : {}".format(vals4))
                        kelurahan_id = self.env['res.village'].sudo().create(vals4)
                        kelurahan_ids.append(kelurahan_id.id)

                        print("kelurahan_id : {}".format(kelurahan_id))
                        print("kelurahan_id.id : {}".format(kelurahan_id.id))

                    self.env['res.subdistrict'].browse(kecamatan_id.id).write({ 'village_ids': kelurahan_ids})
                self.env['res.city'].browse(kota_id.id).write({ 'subdistrict_ids': kecamatan_ids})
            self.env['res.country.state'].browse(prov_id.id).write({ 'city_ids': kota_ids})
################################################################################
