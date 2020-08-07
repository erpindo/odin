# -*- coding: utf-8 -*-

"""Mark as uploaded E-Faktur"""
from datetime import datetime
from odoo import api, fields, models


class UploadEfakturWizard(models.TransientModel):
    """Upload E-Faktur wizard form"""

    _name = "upload.efaktur.wizard"


    def upload_efaktur(self):
        """Function to mark as uploaded E-Faktur"""

        active_ids = self.env.context.get('active_ids')
        efaktur_ids = self.env['efaktur'].browse(active_ids)
        for efaktur in efaktur_ids:
            if efaktur.invoice_id or efaktur.related_picking_id:
                efaktur.write({'validated': True,
                               'date_validated': datetime.now(),
                               'upload_user': self.env.user.id
                               })
