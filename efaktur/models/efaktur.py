# pylint: disable=E501,E0401,R0903
# -*- coding: utf-8 -*-

"""e-Faktur object, inherit account.move and res.partner"""

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Efaktur(models.Model):
    """e-Faktur object with add some field that need in E-Faktur format"""

    _name = "efaktur"

    name = fields.Char('e-Faktur code')
    validated = fields.Boolean(
        'Upload Success', help="centang jika sudah diupload ke e-Pajak",
        default=False)
    invoice_id = fields.Many2one(
        'account.move', 'Invoice',
        help="Hanya akan menampilkan Invoice yang belum mempunyai \
            serial e-Faktur.",
        copy=False, readonly=True)
    date_validated = fields.Datetime('Upload Date', readonly=True)
    npwp_o = fields.Boolean('NPWP000', default=False)
    is_vendor = fields.Boolean('Vendor Bill', readonly=True)
    from_picking = fields.Boolean('From Picking', readonly=True)
    related_picking_id = fields.Many2one(
        'stock.picking', 'Related Picking', readonly=True)
    upload_user = fields.Many2one('res.users', 'Upload User')
    downloaded = fields.Boolean('Downloaded', default=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('efaktur'), index=1)

    def write(self, values):
        """Check e-Faktur id"""
        if values.get('invoice_id') is False:
            inv_ids = self.env['account.move'].search(
                [('efaktur_id', '=', self.id)])
            if inv_ids:
                inv_ids.write({'efaktur_id': False})
        elif values.get('invoice_id'):
            inv = self.env['account.move'].browse(
                [values.get('invoice_id')])
            if not inv.efaktur_id.id:
                inv.write({'efaktur_id': self.id})
                self.invoice_id.write({'efaktur_id': False})
            else:
                raise UserError(_("%s have serial number %s!" %
                                  (inv.number, inv.efaktur_id.name)))
        result = super(Efaktur, self).write(values)
        return result

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Kode e-Faktur tersebut sudah ada!'),
    ]


class AccountMove(models.Model):
    """Inherit account.move to add some e-faktur field and function"""

    _inherit = "account.move"

    efaktur_id = fields.Many2one('efaktur', string="e-Faktur", copy=False)
    tax_number = fields.Char(string="Tax Number")
    replace_invoice_id = fields.Many2one(
        'account.move', string="Replace Invoice")
    efaktur_validated = fields.Boolean(
        string="e-Faktur sudah dikirim ke e-Pajak",
        readonly=True, related='efaktur_id.validated', store=True)
    _sql_constraints = [
        ('name_uniq', 'unique (tax_number)', 'Nomor Pajak sudah ada!'),
    ]

    def action_post(self):
        """Set e-Faktur number after validated"""
        for invoice in self:
            # Invoice yang punya nomor efaktur itu yang customernya
            # adalah Pengusaha Kena Pajak (PKP) yang punya NPWP atau NIK

            # Adalah PKP:
            # if invoice.tax_line_ids and invoice.partner_id.pkp: # <- memasukkan faktor adanya pajak atau enggak
            if invoice.partner_id.pkp: # <- memasukkan faktor adanya pajak atau enggak
            # if invoice.partner_id.pkp:
                # CUSTOMER INVOICE yang belum punya nomor e-faktur:
                if not invoice.efaktur_id and invoice.type == 'out_invoice':
                    _logger.debug("Customer invoice yang belum dapat nomor efaktur")
                    # Yang punya replace invoice
                    if invoice.replace_invoice_id.efaktur_id:
                        # Replace invoice yang efakturnya gak validated
                        if not invoice.replace_invoice_id.efaktur_id.validated:
                            raise ValidationError(_('Invoice pengganti hanya \
                                untuk Invoice yang e-Fakturnya sudah \
                                tervalidasi!'))
                        # Validated
                        else:
                            # e-faktur milik replace invoice diidentifikasi dengan
                            # angka 1 pada digit ketiga nomor e-fakturnya
                            rep_efaktur = invoice.replace_invoice_id.efaktur_id.name
                            new = list(rep_efaktur)
                            new[2] = '1'
                            vals_replaced_efaktur = {
                                'name': self._format_nomor_efaktur(''.join(new)),
                                'invoice_id': invoice.id,
                                'downloaded': False,
                                'validated': False
                            }
                            # 1. Bikin record efaktur baru dengan kode untuk replace invoice
                            efaktur = self.env['efaktur'].create(vals_replaced_efaktur)
                            # 2. Isikan nomor e-faktur ke invoice
                            invoice.write({'efaktur_id': efaktur.id})

                    # Invoice baru / bukan Replace Invoice
                    else:
                        # Digit 2 belum diset
                        if not invoice.partner_id.digit2:
                            raise ValidationError(
                                _('Tidak ada nomor Kode Transaksi di Partner'))
                        # Gass!
                        else:
                            zero = str(0)

                            efaktur = self.env['efaktur'].search([
                                ('invoice_id', '=', False),
                                ('related_picking_id', '=', False),
                                ('company_id', '=', self.env['res.company']._company_default_get('efaktur').id)
                                ], limit=1)

                            if not efaktur:
                                raise ValidationError(
                                    _('Tidak tersedia kode e-Faktur yang bisa digunakan. Silakan generate kode terlebih dahulu.'))

                            if not invoice.partner_id.npwp and not invoice.partner_id.nik:
                                raise ValidationError(
                                    _("Nomor NPWP dan NIK customer belum tercatat. Silakan isi NPWP atau NIK terlebih dahulu."))

                            # 1. Edit nomor invoice dengan yang sudah disertai kode 2 digit
                            nomor_efaktur_string = \
                                str(invoice.partner_id.digit2) +\
                                str(zero) +\
                                str(efaktur.name)
                            nomor_efaktur_string = self._format_nomor_efaktur(nomor_efaktur_string)
                            efaktur.write({
                                'invoice_id': invoice.id,
                                'name': nomor_efaktur_string
                                })
                            # 2. Isikan nomor e-faktur ke invoice
                            invoice.write({'efaktur_id': efaktur.id})

                # # VENDOR BILL: punya tax number tapi belum punya nomor e-faktur
                # if invoice.tax_number and invoice.type == 'in_invoice' and \
                #         not invoice.efaktur_id:
                #     vals_efaktur_bill = {
                #         'name': invoice.tax_number,
                #         'invoice_id': invoice.id,
                #         'is_vendor': True,
                #     }
                #     # 1. Bikin record efaktur baru pakai tax number
                #     efakturs = self.env['efaktur'].create(vals_efaktur_bill)
                #     # 2. Isikan nomor e-faktur ke bill
                #     invoice.write({'efaktur_id': efakturs.id})

            # Bukan PKP
            else:
                _logger.debug("NOT (invoice.tax_line_ids and invoice.partner_id.pkp)")

        return super(AccountMove, self).action_post()

    def _format_nomor_efaktur(self, nomor):
        """"Format nomor e-faktur dengan pola: 000.000-00.00000000"""
        return "{}.{}-{}.{}".format(nomor[:3], nomor[3:6], nomor[6:8], nomor[-8:])

    def action_cancel(self):
        """Canceling or unlink E-Faktur"""
        res = super(AccountMove, self).action_cancel()
        if self.tax_number and self.type == 'in_invoice' and self.efaktur_id:
            self.efaktur_id.sudo().unlink()
        return res

    def _name_get(self):
        """Get name"""
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Refund'),
            'in_refund': _('Vendor Refund'),
        }
        result = []
        for inv in self:
            if inv.state == 'cancel':
                result.append((inv.id,
                              "Cancelled %s %s" % (inv.move_name
                                                   or TYPES[inv.type],
                                                   inv.name or '')))
            else:
                result.append((inv.id, "%s %s" %
                               (inv.number or TYPES[inv.type],
                                inv.name or '')))
        return result

    def reset_efaktur(self):
        """To reset E-Faktur, so it can be use for other invoice"""
        for faktur in self:
            obj_faktur = faktur.efaktur_id
            no_faktur_terformat = faktur.efaktur_id.name

            no_faktur_reset = ''.join(no_faktur_terformat.split('-'))
            no_faktur_reset = ''.join(no_faktur_reset.split('.'))

            # Reset record efaktur di model aslinya
            obj_faktur.write({
                'name': no_faktur_reset[-13:],
                'validate': False,
                'invoice_id': False,
                'npwp_o': False,
                'downloaded': False
            })

            faktur.message_post(
                body='e-Faktur Reset: %s ' % (no_faktur_terformat,),
                subject="Reset Efaktur")

            # Nomor efaktur di invoice dihilangkan
            faktur.write({'efaktur_id': False})
        return True


class ResPartner(models.Model):
    """Inherit res.partner object to add NPWP field and Kode Transaksi"""
    _inherit = "res.partner"

    pkp = fields.Boolean(default=False)
    npwp = fields.Char(string='NPWP', track_visibility='onchange')
    nik = fields.Char(string='NIK', track_visibility='onchange')
    digit2 = fields.Selection([
        ('01', '01 Kepada Pihak yang Bukan Pemungut PPN (Customer Biasa)'),
        ('02', '02 Kepada Pemungut Bendaharawan (Dinas Kepemerintahan)'),
        ('03', '03 Kepada Pemungut Selain Bendaharawan (BUMN)'),
        ('04', '04 DPP Nilai Lain (PPN 1%)'),
        ('06', '06 Penyerahan Lainnya (Turis Asing)'),
        ('07', '07 Penyerahan yang PPN-nya Tidak Dipungut \
            (Kawasan Ekonomi Khusus/ Batam)'),
        ('08', '08 Penyerahan yang PPN-nya Dibebaskan \
            (Impor Barang Tertentu)'),
        ('09', '09 Penyerahan Aktiva ( Pasal 16D UU PPN )'),
    ], string='Kode Transaksi', help='Dua digit pertama nomor pajak',
        track_visibility='onchange')

    tax_address = fields.Char('Tax Address', track_visibility='onchange')
    tax_name = fields.Char('Tax Name', track_visibility='onchange')
