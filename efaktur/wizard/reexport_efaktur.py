# -*- coding: utf-8 -*-

"""Generate E-Faktur with excel format"""
from datetime import datetime
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MakeObj(dict):
    """Make object"""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


class ReexportEFaktur(models.TransientModel):
    """Wizard form view of generate E-Faktur"""

    _name = 'reexport.efaktur'

    state_x = fields.Selection(
        [('choose', 'choose'), ('get', 'get')], default='choose')
    data_x = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    delimiter = fields.Selection([(',', 'comma'), (';', 'semicolon')],
                                 string='Delimiter', default=',')
    npwp_o = fields.Boolean('NPWP000', default=False)

    def reexport_efaktur(self):
        """Collect the data and execute function _generate_efaktur"""

        data = {}
        active_ids = self.env.context.get('active_ids')
        tax_ids = self.env['efaktur'].browse(active_ids)
        delimiter = self.delimiter

        # From Invoice of Customer
        invoice_ids = [inv.invoice_id.id for inv in tax_ids
                       if inv.invoice_id.id and not inv.is_vendor]
        # From Invoice of Supplier
        vendor_bill_ids = [inv.invoice_id.id for inv in tax_ids
                           if inv.invoice_id.id and inv.is_vendor]

        data.update({
            'invoice_ids': invoice_ids,
            'vendor_bill_ids': vendor_bill_ids,
        })

        for mod in tax_ids:
            mod.npwp_o = self.npwp_o
        return self._generate_efaktur(data, delimiter)

    def _generate_efaktur_invoice(self, data, delimiter, output_head):
        print ("masuk sini............")
        """Generate E-Faktur for customer invoice"""

        # Invoice of Customer
        obj_invs = self.env['account.move'].browse(data['invoice_ids'])
        print ("obj_invs",obj_invs)

        eTax = MakeObj(self._prepare_etax())
        print ("etax",eTax)
        efaktur_values = self._prepare_efaktur_csv(delimiter)
        print ("efaktur_values", efaktur_values)

        for obj_inv in obj_invs:
            company_id = obj_inv.efaktur_id.company_id
            # If state open then print invoice line
            if obj_inv.state in ('open', 'paid'):
                invoice_date = datetime.strptime(
                    str(obj_inv.date_invoice), "%Y-%m-%d") or False

                invoice_npwp = nik = street = street2 = number_ref = ''
                if not obj_inv.partner_id.npwp or self.npwp_o:
                    nik = str(obj_inv.partner_id.nik)

                if obj_inv.replace_invoice_id:
                    number_ref = str(obj_inv.replace_invoice_id.number) + \
                        " replaced by " + str(obj_inv.number) + " " + nik
                else:
                    number_ref = str(obj_inv.number) + " " + nik

                if not invoice_date:
                    raise UserError(_("Invoice %s no date", (obj_inv.number)))

                if not obj_inv.partner_id.street:
                    street = ''
                else:
                    street = "" + obj_inv.partner_id.street

                if not obj_inv.partner_id.street2:
                    street2 = ''
                else:
                    street2 = ", " + obj_inv.partner_id.street2

                basic_address = ("" + street + street2) or '' \
                    if eTax.fields.npwp.value == '000000000000000' else \
                    obj_inv.partner_id.tax_address \
                    or ("" + street + street2) or ''
                city = obj_inv.partner_id.city or '' \
                    if eTax.fields.npwp.value == '000000000000000' else ''
                state = obj_inv.partner_id.state_id.name or '' \
                    if eTax.fields.npwp.value == '000000000000000' else ''
                zip_code = obj_inv.partner_id.zip or '' \
                    if eTax.fields.npwp.value == '000000000000000' else ''
                country = obj_inv.partner_id.country_id.name or '' \
                    if eTax.fields.npwp.value == '000000000000000' else ''

                if self.npwp_o:
                    invoice_npwp = '000000000000000'
                else:
                    invoice_npwp = '000000000000000'
                    if obj_inv.partner_id.npwp and len(obj_inv.partner_id.npwp) >= 12:
                        invoice_npwp = obj_inv.partner_id.npwp
                    elif not obj_inv.partner_id.npwp or (obj_inv.partner_id.npwp and
                                                         len(obj_inv.partner_id.npwp) < 12) and obj_inv.partner_id.nik:
                        invoice_npwp = obj_inv.partner_id.nik
                    invoice_npwp = invoice_npwp.replace('.', '')
                    invoice_npwp = invoice_npwp.replace('-', '')

                '''
                    Here all fields or columns based on eTax Invoice Third Party
                '''
                no_efaktur_unformat = obj_inv.efaktur_id.name.replace('.', '').replace('-', '')
                eTax.fields.kd_jenis_transaksi.value = no_efaktur_unformat[0:2] or ''
                eTax.fields.fg_pengganti.value = no_efaktur_unformat[2] or ''
                eTax.fields.nomor_faktur.value = no_efaktur_unformat[3:] or ''

                eTax.fields.masa_pajak.value = datetime.strptime(str(obj_inv.date_invoice),
                                                                 "%Y-%m-%d").month or False
                eTax.fields.tahun_pajak.value = datetime.strptime(str(obj_inv.date_invoice),
                                                                  "%Y-%m-%d").year or False
                eTax.fields.tgl_faktur.value = '{0}/{1}/{2}'.format(invoice_date.day,
                                                                    invoice_date.month,
                                                                    invoice_date.year) or ''
                eTax.fields.npwp.value = invoice_npwp
                eTax.fields.nama.value = obj_inv.partner_id.name if \
                    eTax.fields.npwp.value == '000000000000000' else obj_inv.partner_id.tax_name \
                    or obj_inv.partner_id.name or ''
                eTax.fields.alamat_lengkap.value = '%s %s %s %s %s' % (
                    basic_address,
                    city,
                    state,
                    zip_code,
                    country,
                )
                eTax.fields.jumlah_dpp.value = int(
                    round(obj_inv.amount_untaxed, 0)) or 0.0
                eTax.fields.jumlah_ppn.value = int(
                    round(obj_inv.amount_tax, 0)) or 0.0
                eTax.fields.id_keterangan_tambahan.value = '1' if \
                    obj_inv.partner_id.digit2 == '07' else ''
                eTax.fields.referensi.value = number_ref

                company_npwp = ''
                if company_id.partner_id.npwp:
                    company_npwp = company_id.partner_id.npwp
                else:
                    company_npwp = '000000000000000'

                efaktur_values.update({
                    'fk_value':
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        % (
                            'FK', delimiter,
                            eTax.fields.kd_jenis_transaksi.value, delimiter,
                            eTax.fields.fg_pengganti.value, delimiter,
                            eTax.fields.nomor_faktur.value, delimiter,
                            eTax.fields.masa_pajak.value, delimiter,
                            eTax.fields.tahun_pajak.value, delimiter,
                            eTax.fields.tgl_faktur.value, delimiter,
                            eTax.fields.npwp.value, delimiter,
                            eTax.fields.nama.value, delimiter,
                            eTax.fields.alamat_lengkap.value, delimiter,
                            eTax.fields.jumlah_dpp.value, delimiter,
                            eTax.fields.jumlah_ppn.value, delimiter,
                            eTax.fields.jumlah_ppnbm.value, delimiter,
                            eTax.fields.id_keterangan_tambahan.value, delimiter,
                            eTax.fields.fg_uang_muka.value, delimiter,
                            eTax.fields.uang_muka_dpp.value, delimiter,
                            eTax.fields.uang_muka_ppn.value, delimiter,
                            eTax.fields.uang_muka_ppnbm.value, delimiter,
                            eTax.fields.referensi.value, delimiter,
                        ),
                    'lt_value':
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        % (
                            'FAPR', delimiter,
                            company_npwp, delimiter,
                            company_id.name, delimiter,
                            company_id.partner_id.street, delimiter,
                            eTax.fields.blok.value, delimiter,
                            eTax.fields.nomor.value, delimiter,
                            eTax.fields.rt.value, delimiter,
                            eTax.fields.rw.value, delimiter,
                            eTax.fields.kecamatan.value, delimiter,
                            eTax.fields.kelurahan.value, delimiter,
                            eTax.fields.kabupaten.value, delimiter,
                            eTax.fields.propinsi.value, delimiter,
                            eTax.fields.kode_pos.value, delimiter,
                            eTax.fields.nomor_telp.value, delimiter,
                        )
                })

                output_head = '%s\n%s\n%s\n' % (
                    output_head,
                    efaktur_values.get('fk_value'),
                    efaktur_values.get('lt_value'),
                )

                # HOW TO ADD 2 line to 1 line for free product
                line_sorted = sorted(
                    obj_inv.invoice_line_ids, key=lambda a: a.product_id)

                free, sales, tax_status = [], [], {
                    'included': False, 'excluded': False}

                for obj_inv_line in line_sorted:
                    '''
                        *invoice_line_unit_price is price unit use for harga_satuan's column
                        *invoice_line_quantity is quantity use for jumlah_barang's column
                        *invoice_line_total_price is bruto price use for harga_total's column
                        *invoice_line_discount_m2m is discount price use for diskon's column
                        *obj_inv_line.price_subtotal is subtotal price use for dpp's column
                        *tax_line or free_tax_line is tax price use for ppn's column
                    '''

                    invoice_line_unit_price = free_tax_line = tax_line = bruto_total = \
                        diff_bruto = diff_disc = total_discount = 0.0
                    invoice_line_default_code = obj_inv_line.product_id.default_code or ''
                    invoice_line_name = obj_inv_line.product_id.name or ''
                    invoice_line_quantity = obj_inv_line.quantity

                    for tax in obj_inv_line.invoice_line_tax_ids:
                        if tax.amount > 0:
                            if tax.price_include:
                                tax_status.update({'included': True})
                                invoice_line_unit_price = obj_inv_line.price_unit
                            else:
                                tax_status.update({'excluded': True})
                                invoice_line_unit_price = obj_inv_line.price_unit

                            tax_line += obj_inv_line.price_subtotal * \
                                (tax.amount / 100.0)

                    if not obj_inv_line.invoice_line_tax_ids:
                        invoice_line_unit_price = obj_inv_line.price_unit

                    invoice_line_total_price = invoice_line_unit_price * invoice_line_quantity

                    if tax_status.get('included'):
                        invoice_line_discount_m2m = invoice_line_total_price - \
                            (obj_inv_line.price_subtotal + round(tax_line, 2))
                        if invoice_line_discount_m2m < 0:
                            invoice_line_discount_m2m = 0.0
                    else:
                        invoice_line_discount_m2m = invoice_line_total_price\
                            - obj_inv_line.price_subtotal

                    if obj_inv_line.price_subtotal < 0:
                        for tax in obj_inv_line.invoice_line_tax_ids:
                            free_tax_line += (obj_inv_line.price_subtotal *
                                              (tax.amount / 100.0)) * -1.0

                        free.append({
                            'default_code': invoice_line_default_code,
                            'name': invoice_line_name,
                            'unit_price': invoice_line_unit_price,
                            'quantity': invoice_line_quantity,
                            'bruto': invoice_line_total_price,
                            'subtotal': obj_inv_line.price_subtotal,
                            'discount': invoice_line_total_price - obj_inv_line.price_subtotal,
                            'sale_line_ids': obj_inv_line.sale_line_ids.ids,
                            'order_id': obj_inv_line.sale_line_ids[0].order_id if
                            obj_inv_line.sale_line_ids else False,
                            'ppn': free_tax_line,
                            'product_id': obj_inv_line.product_id.id,
                        })
                    elif obj_inv_line.price_subtotal != 0.0:
                        sales.append({
                            'default_code': invoice_line_default_code,
                            'name': invoice_line_name,
                            'unit_price': invoice_line_unit_price,
                            'quantity': invoice_line_quantity,
                            'bruto': invoice_line_total_price,
                            'subtotal': obj_inv_line.price_subtotal,
                            'discount': invoice_line_discount_m2m,
                            'sale_line_ids': obj_inv_line.sale_line_ids.ids,
                            'order_id': obj_inv_line.sale_line_ids[0].order_id if
                            obj_inv_line.sale_line_ids else False,
                            'ppn': tax_line,
                            'product_id': obj_inv_line.product_id.id,
                        })

                sub_total_before_adjustment = sub_total_ppn_before_adjustment = 0.0

                '''
                    We are finding the product that has affected
                    by free product to adjustment the calculation
                of discount and subtotal.
                    - the price total of free product will be
                    included as a discount to related of product.
                '''
                for sale in sales:
                    for f in free:
                        if f['product_id'] == sale['product_id'] and \
                                f['order_id'] == sale['order_id']:
                            sale['discount'] = sale['discount'] + \
                                (f['subtotal'] * -1.0) + f['ppn']
                            sale['subtotal'] = sale['subtotal'] - \
                                (f['subtotal'] * -1.0)

                            tax_line = 0

                            for tax in obj_inv_line.invoice_line_tax_ids:
                                if tax.amount > 0:
                                    tax_line += sale['subtotal'] * \
                                        (tax.amount / 100.0)

                            sale['ppn'] = tax_line

                            free.remove(f)

                    sub_total_before_adjustment += sale['subtotal']
                    sub_total_ppn_before_adjustment += sale['ppn']
                    bruto_total += sale['bruto']
                    total_discount += round(sale['discount'], 2)

                '''
                    We are collecting the list of DPP & PPN which has amount greather than 0.0
                and will be accessing by pass index directly as @params.
                '''
                sales_by_subtotal = [index for (index, sale) in
                                     enumerate(sales) if sale["subtotal"] > 0.0]
                sales_by_ppn = [index for (index, sale) in enumerate(
                    sales) if sale["ppn"] > 0.0]

                _logger.info('CHECK SBS ? : %s, CHECK INVOICE DPP : %s, CHECK INVOICE PPN : %s' % (
                    sales_by_subtotal, eTax.fields.jumlah_dpp.value, eTax.fields.jumlah_ppn.value
                ))

                if not sales_by_ppn:
                    first_ppn = 0.0
                else:
                    first_ppn = sales[sales_by_ppn[0]]['ppn']

                if not sales_by_subtotal:
                    first_dpp = 0.0
                else:
                    first_dpp = sales[sales_by_subtotal[0]]['subtotal']

                first_bruto = sales[0]['bruto']
                first_disc = round(sales[0]['discount'], 2)

                diff_dpp = eTax.fields.jumlah_dpp.value - sub_total_before_adjustment
                diff_ppn = eTax.fields.jumlah_ppn.value - sub_total_ppn_before_adjustment

                if tax_status.get('included') and tax_status.get('excluded'):
                    if total_discount > 0.0:
                        warning_mess = {
                            'title': _('Warning Notification!'),
                            'message': _('There are Invoice Line have more tax type \
                                            include and exclude : %s', (obj_inv.number))
                        }
                        return {'warning': warning_mess}
                elif tax_status.get('excluded'):
                    if total_discount > 0.0:
                        diff_disc = (
                            bruto_total - (eTax.fields.jumlah_dpp.value)) - total_discount
                        diff_bruto = eTax.fields.jumlah_dpp.value - \
                            (bruto_total - total_discount)
                    else:
                        diff_bruto = eTax.fields.jumlah_dpp.value - bruto_total

                    diff_bruto = diff_bruto * \
                        (-1.0) if diff_bruto < 0.0 else diff_bruto
                elif tax_status.get('included'):
                    diff_disc = 0.0
                    diff_bruto = 0.0  # No Adjustment

                '''
                    We will adjust Bruto, DPP, PPN and Discount column if there is differential
                due to Rounding.
                '''

                # Adjustment Bruto
                if diff_bruto != 0.0:
                    first_bruto += diff_bruto

                # Adjustment DPP
                if diff_dpp != 0.0:
                    first_dpp += diff_dpp

                # Adjustment PPN
                if diff_ppn != 0:
                    first_ppn += diff_ppn

                # Adjustment Disount Total End
                if diff_disc != 0:
                    first_disc += diff_disc

                sales[0]['bruto'] = first_bruto
                sales[0]['discount'] = first_disc
                sales[sales_by_subtotal[0]
                      if sales_by_subtotal else 0]['subtotal'] = first_dpp
                sales[sales_by_ppn[0] if sales_by_ppn else 0]['ppn'] = first_ppn

                for sale in sales:
                    output_head += '"OF"' + delimiter + '\"' + sale['default_code'] + \
                        '\"' + delimiter + '\"' + sale['name'] + '\"' + delimiter + '\"' + \
                        str(sale['unit_price']) + '\"' + delimiter + '\"' + \
                        str(sale['quantity']) + \
                        '\"' + delimiter + '\"' + \
                        str(sale['bruto']) + '\"' + delimiter
                    output_head += '\"' + str(round(sale['discount'], 2)) + '\"' + delimiter + \
                        '\"' + str(sale['subtotal']) + '\"' + delimiter + '\"' + \
                        str(sale['ppn']) + \
                        '\"' + delimiter + '0' + delimiter + '0' + delimiter
                    output_head += delimiter + '' + delimiter + '' + delimiter + '' + delimiter + \
                        '' + delimiter + '' + delimiter + '' + delimiter + '' + '\n'

        active_ids = self.env.context.get('active_ids')
        download_ids = self.env['efaktur'].browse(active_ids)
        download_ids.write({'downloaded': True})

        return output_head


    def _generate_efaktur_purchase(self, data, delimiter, output_head):
        """Generate E-Faktur for Purchase / Vendor Bills"""

        # Invoice of Supplier
        obj_invs = self.env['account.move'].browse(data['vendor_bill_ids'])
        output_head = 'FK' + delimiter + 'KD_JENIS_TRANSAKSI' + delimiter + \
            'FG_PENGGANTI' + delimiter + 'NOMOR_FAKTUR' + delimiter + 'MASA_PAJAK' + \
            delimiter + 'TAHUN_PAJAK' + delimiter
        output_head += 'TANGGAL_FAKTUR' + delimiter + 'NPWP' + delimiter + \
            'NAMA' + delimiter + 'ALAMAT_LENGKAP' + delimiter + 'JUMLAH_DPP' + \
            delimiter + 'JUMLAH_PPN' + delimiter
        output_head += 'JUMLAH_PPNBM' + delimiter + 'ID_KETERANGAN_TAMBAHAN' + \
            delimiter + 'FG_UANG_MUKA' + delimiter + 'UANG_MUKA_DPP' + delimiter + \
            'UANG_MUKA_PPN' + delimiter + 'UANG_MUKA_PPNBM' + delimiter + 'REFERENSI'
        output_head += '\n'

        for obj_inv in obj_invs:  # browse data invoice based id dictionary
            # if state open then print invoice line
            if obj_inv.state in ('open', 'paid'):
                invoice_number = obj_inv.efaktur_id.name or ''
                invoice_date = datetime.strptime(
                    str(obj_inv.date_invoice), "%Y-%m-%d") or False
                if not invoice_date:
                    raise UserError(_("Invoice %s no date", (invoice_number)))
                invoice_date_p = '{0}/{1}/{2}'.format(invoice_date.day,
                                                      invoice_date.month, invoice_date.year) or ''

                invoice_npwp = street = street2 = ''

                if self.npwp_o == True:
                    invoice_npwp = '000000000000000'
                else:
                    invoice_npwp = obj_inv.partner_id.npwp or '000000000000000'
                    invoice_npwp = invoice_npwp.replace('.', '')
                    invoice_npwp = invoice_npwp.replace('-', '')

                if invoice_number:
                    invoice_number = invoice_number.replace('.', '')
                    invoice_number = invoice_number.replace('-', '')

                invoice_DPP = int(round(obj_inv.amount_untaxed, 0)) or ''

                total_tax_line_amount = 0.0

                for tax_line in obj_inv.tax_line_ids:
                    total_tax_line_amount += tax_line.amount

                invoice_PPN = int(total_tax_line_amount)

                if not obj_inv.partner_id.street:
                    street = ''
                else:
                    street = "" + obj_inv.partner_id.street

                if not obj_inv.partner_id.street2:
                    street2 = ''
                else:
                    street2 = ", " + obj_inv.partner_id.street2

                if invoice_npwp == '000000000000000':
                    invoice_customer = obj_inv.partner_id.name
                    invoice_customer_address = ("" + street + street2) or ''
                    invoice_customer_city = obj_inv.partner_id.city or ''
                    invoice_customer_state = obj_inv.partner_id.state_id.name or ''
                    invoice_customer_zip = obj_inv.partner_id.zip or ''
                    invoice_customer_country = obj_inv.partner_id.country_id.name or ''

                else:
                    invoice_customer = obj_inv.partner_id.tax_name or obj_inv.partner_id.name
                    invoice_customer_address = obj_inv.partner_id.tax_address \
                        or ("" + street + street2) or ''
                    invoice_customer_city = ''
                    invoice_customer_state = ''
                    invoice_customer_zip = ''
                    invoice_customer_country = ''

                    if invoice_customer == False:
                        invoice_customer = ''

                output_head += 'FM' + delimiter + '\"' + invoice_number[0:2] + \
                    '\"' + delimiter + invoice_number[2] + delimiter + '\"' + \
                    invoice_number[3:] + '\"' + delimiter + str(invoice_date.month) + \
                    delimiter + str(invoice_date.year) + delimiter
                output_head += '\"' + str(invoice_date_p) + '\"' + delimiter + \
                    '\"' + str(invoice_npwp) + '\"' + delimiter + '\"' + \
                    str(invoice_customer) + '\"' + delimiter + '\"' + \
                    invoice_customer_address + ' ' + invoice_customer_city + \
                    ' ' + str(invoice_customer_state) + ' ' + invoice_customer_zip + ' ' + \
                    str(invoice_customer_country) + '\"' + delimiter
                output_head += str(invoice_DPP) + delimiter + str(invoice_PPN) + \
                    delimiter + '0' + delimiter + '1\n'

        active_ids = self.env.context.get('active_ids')
        download_ids = self.env['efaktur'].browse(active_ids)
        download_ids.write({'downloaded': True})

        return output_head

    def _prepare_etax(self):
        """Prepare Etax"""
        eTax_vals = {
            'fields': MakeObj({
                'fk': MakeObj({
                    'label': 'FK',
                    'value': 'FK',
                }),
                'lt': MakeObj({
                    'label': 'LT',
                    'value': 'LT',
                }),
                'of': MakeObj({
                    'label': 'OF',
                    'value': 'OF',
                }),
                'kd_jenis_transaksi': MakeObj({
                    'label': 'KD_JENIS_TRANSAKSI',
                    'value': 0,
                }),
                'fg_pengganti': MakeObj({
                    'label': 'FG_PENGGANTI',
                    'value': 0,
                }),
                'nomor_faktur': MakeObj({
                    'label': 'NOMOR_FAKTUR',
                    'value': 0,
                }),
                'masa_pajak': MakeObj({
                    'label': 'MASA_PAJAK',
                    'value': '',
                }),
                'tahun_pajak': MakeObj({
                    'label': 'TAHUN_PAJAK',
                    'value': '',
                }),
                'tgl_faktur': MakeObj({
                    'label': 'TANGGAL_FAKTUR',
                    'value': '',
                }),
                'npwp': MakeObj({
                    'label': 'NPWP',
                    'value': '',
                }),
                'nama': MakeObj({
                    'label': 'NAMA',
                    'value': '',
                }),
                'alamat_lengkap': MakeObj({
                    'label': 'ALAMAT_LENGKAP',
                    'value': '',
                }),
                'jumlah_dpp': MakeObj({
                    'label': 'JUMLAH_DPP',
                    'value': 0,
                }),
                'jumlah_ppn': MakeObj({
                    'label': 'JUMLAH_PPN',
                    'value': 0,
                }),
                'jumlah_ppnbm': MakeObj({
                    'label': 'JUMLAH_PPNBM',
                    'value': 0,
                }),
                'id_keterangan_tambahan': MakeObj({
                    'label': 'ID_KETERANGAN_TAMBAHAN',
                    'value': '',
                }),
                'fg_uang_muka': MakeObj({
                    'label': 'FG_UANG_MUKA',
                    'value': 0,
                }),
                'uang_muka_dpp': MakeObj({
                    'label': 'UANG_MUKA_DPP',
                    'value': 0,
                }),
                'uang_muka_ppn': MakeObj({
                    'label': 'UANG_MUKA_PPN',
                    'value': 0,
                }),
                'uang_muka_ppnbm': MakeObj({
                    'label': 'UANG_MUKA_PPNBM',
                    'value': 0,
                }),
                'referensi': MakeObj({
                    'label': 'REFERENSI',
                    'value': '',
                }),
                'jalan': MakeObj({
                    'label': 'JALAN',
                    'value': '',
                }),
                'blok': MakeObj({
                    'label': 'BLOK',
                    'value': '',
                }),
                'nomor': MakeObj({
                    'label': 'NOMOR',
                    'value': '',
                }),
                'rt': MakeObj({
                    'label': 'RT',
                    'value': ''
                }),
                'rw': MakeObj({
                    'label': 'RW',
                    'value': '',
                }),
                'kecamatan': MakeObj({
                    'label': 'KECAMATAN',
                    'value': ''
                }),
                'kelurahan': MakeObj({
                    'label': 'KELURAHAN',
                    'value': ''
                }),
                'kabupaten': MakeObj({
                    'label': 'KABUPATEN',
                    'value': '',
                }),
                'propinsi': MakeObj({
                    'label': 'PROPINSI',
                    'value': ''
                }),
                'kode_pos': MakeObj({
                    'label': 'KODE_POS',
                    'value': '',
                }),
                'nomor_telp': MakeObj({
                    'label': 'NOMOR_TELEPON',
                    'value': '',
                }),
                'kode_object': MakeObj({
                    'label': 'KODE_OBJEK',
                    'value': '',
                }),
                'harga_satuan': MakeObj({
                    'label': 'HARGA_SATUAN',
                    'value': 0,
                }),
                'jumlah_brg': MakeObj({
                    'label': 'JUMLAH_BARANG',
                    'value': 0,
                }),
                'harga_total': MakeObj({
                    'label': 'HARGA_TOTAL',
                    'value': 0,
                }),
                'diskon': MakeObj({
                    'label': 'DISKON',
                    'value': 0,
                }),
                'dpp': MakeObj({
                    'label': 'DPP',
                    'value': 0,
                }),
                'ppn': MakeObj({
                    'label': 'PPN',
                    'value': 0,
                }),
                'tarif_ppnbm': MakeObj({
                    'label': 'TARIF_PPNBM',
                    'value': 0,
                }),
                'ppnbm': MakeObj({
                    'label': 'PPNBM',
                    'value': 0,
                }),
            }),
        }
        return eTax_vals

    def _prepare_efaktur_csv(self, delimiter):
        eTax = MakeObj(self._prepare_etax())

        efaktur_values = {
            'fk_head':
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                % (
                    eTax.fields.fk.label, delimiter,
                    eTax.fields.kd_jenis_transaksi.label, delimiter,
                    eTax.fields.fg_pengganti.label, delimiter,
                    eTax.fields.nomor_faktur.label, delimiter,
                    eTax.fields.masa_pajak.label, delimiter,
                    eTax.fields.tahun_pajak.label, delimiter,
                    eTax.fields.tgl_faktur.label, delimiter,
                    eTax.fields.npwp.label, delimiter,
                    eTax.fields.nama.label, delimiter,
                    eTax.fields.alamat_lengkap.label, delimiter,
                    eTax.fields.jumlah_dpp.label, delimiter,
                    eTax.fields.jumlah_ppn.label, delimiter,
                    eTax.fields.jumlah_ppnbm.label, delimiter,
                    eTax.fields.id_keterangan_tambahan.label, delimiter,
                    eTax.fields.fg_uang_muka.label, delimiter,
                    eTax.fields.uang_muka_dpp.label, delimiter,
                    eTax.fields.uang_muka_ppn.label, delimiter,
                    eTax.fields.uang_muka_ppnbm.label, delimiter,
                    eTax.fields.referensi.label, delimiter,
                ),
            'lt_head':
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                % (
                    eTax.fields.lt.label, delimiter,
                    eTax.fields.npwp.label, delimiter,
                    eTax.fields.nama.label, delimiter,
                    eTax.fields.jalan.label, delimiter,
                    eTax.fields.blok.label, delimiter,
                    eTax.fields.nomor.label, delimiter,
                    eTax.fields.rt.label, delimiter,
                    eTax.fields.rw.label, delimiter,
                    eTax.fields.kecamatan.label, delimiter,
                    eTax.fields.kelurahan.label, delimiter,
                    eTax.fields.kabupaten.label, delimiter,
                    eTax.fields.propinsi.label, delimiter,
                    eTax.fields.kode_pos.label, delimiter,
                    eTax.fields.nomor_telp.label, delimiter,
                ),
            'of_head':
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                '"%s"%s'
                % (
                    eTax.fields.of.label, delimiter,
                    eTax.fields.kode_object.label, delimiter,
                    eTax.fields.nama.label, delimiter,
                    eTax.fields.harga_satuan.label, delimiter,
                    eTax.fields.jumlah_brg.label, delimiter,
                    eTax.fields.harga_total.label, delimiter,
                    eTax.fields.diskon.label, delimiter,
                    eTax.fields.dpp.label, delimiter,
                    eTax.fields.ppn.label, delimiter,
                    eTax.fields.tarif_ppnbm.label, delimiter,
                    eTax.fields.ppnbm.label, delimiter,
                ),
        }

        return efaktur_values


    def _generate_efaktur(self, data, delimiter):
        """Main function of generate E-Faktur from wizard"""

        filename = 'reexport_efaktur.csv'

        efaktur_values = self._prepare_efaktur_csv(delimiter)

        _logger.info('EFAKTUR VALUES %s' % (efaktur_values))

        output_head = '%s\n%s\n%s' % (
            efaktur_values.get('fk_head'),
            efaktur_values.get('lt_head'),
            efaktur_values.get('of_head'),
        )

        output_head = self._generate_efaktur_invoice(
            data, delimiter, output_head)

        output_head2 = ''
        output_head2 = self._generate_efaktur_purchase(
            data, delimiter, output_head2)

        if data['vendor_bill_ids']:
            my_utf8 = output_head2.encode("utf-8")
        else:
            my_utf8 = output_head.encode("utf-8")
        out = base64.b64encode(my_utf8)

        self.write({'state_x': 'get', 'data_x': out, 'name': filename})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=reexport.efaktur&field=data_x&filename_field=name&id=%s&download=true&filename=%s' % (self.id, filename,),
            'target': 'self',
        }
