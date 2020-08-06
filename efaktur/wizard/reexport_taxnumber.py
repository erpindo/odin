# pylint: disable=E0401,R0903
# -*- coding: utf-8 -*-
"""Generate Tax Number"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReexportTaxnumber(models.TransientModel):
    """Generate Tax Number"""

    _name = 'reexport.taxnumber'

    name = fields.Char('Filename', readonly=True)
    start_number = fields.Char('Start Number')
    end_number = fields.Char('End Number')


    def generate_number(self):
        """Function to generate tax number"""

        start_int = self.start_number
        end_int = self.end_number

        start_num = int(start_int)
        end_num = int(end_int)

        term = end_num - start_num

        if len(self.start_number) == 13 and len(self.end_number) == 13:
            #             raise Warning("must 13")
            if start_int[:5] == end_int[:5]:
                if int(start_int[-8:]) < int(end_int[-8:]) and term <= 20000:
                    while start_num <= end_num:
                        zero_first_len = len(start_int) - len(str(start_num))
                        i = 1
                        zero_first = ''
                        while i <= zero_first_len:
                            zero_first += '0'
                            i += 1

                        res_value = zero_first + str(start_num)
                        values = {'name': res_value}
                        self.env['efaktur'].create(values)
                        start_num += 1
                else:
                    raise UserError(_(" last 8 digit of End Number should be greater than \
                        last 8 digit of Start Number && 8 digit of End Number MINUS 8 digit \
                        of Start Number no greater than 10.000"))
            else:
                raise UserError(
                    _(" 1st of 5 digit should be same of Start Number and End Number."))
        else:
            raise UserError(_("total digit should be 13."))
