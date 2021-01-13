from openerp import fields,models,api,_
import csv
import os
from io import StringIO
import logging
import base64
import openerp.exceptions
from tempfile import TemporaryFile
from datetime import datetime
_logger = logging.getLogger(__name__)


class customerUploadCSV(models.TransientModel):
    _name = 'customer.upload.csv'
    _description = "Customer upload csv"

    file_upload=fields.Binary(string="File")


    @api.multi
    def customer_invoice_upload_csv(self):
        csv_datas = self.file_upload
        print("fileeeeeeeee",csv_datas)
        fileobj = TemporaryFile('wb+')
        csv_datas = base64.decodestring(csv_datas)
        fileobj.write(csv_datas)
        fileobj.seek(0)
        str_csv_data = fileobj.read().decode('utf-8')
        lis = csv.reader(StringIO(str_csv_data), delimiter=',')
        print("lisssssssssssssss",lis)
        rownum = 0
        faulty_rows = []
        header = ''
        cust_invoice_numbers = {}
        invocie_list = []
        for row in lis:
            invoice_status = {}
            # contract_vals ={}
            try:
                if rownum == 0:
                    header = row
                else:
                    if not row:
                        continue
                    _logger.error('------------rownum---------- %s', rownum)

                    # inv_no = row[1].strip()
                    customer = row[5].strip()
                    product = row[2].strip()
                    inv_date = row[0].strip()
                    # str5=inv_date +'00.00.00'
                    # print(str5)
                    # due_date = row[2].strip()
                    # so_source = row[6].strip()
                    # user =row[3].strip()
                    # name_des= row[3].split(' -')[0]
                    # pri_unit = float(row[3].split('$')[1].split('/')[0])
                    # qua = row[3].split(' -')[1].split(' hr')[0]
                    # # str2 = float(qua.replace(':', '.'))


                    if inv_date:
                        date_invoice = datetime.strptime(inv_date,'%b %d, %Y').strftime('%Y-%m-%d')
                        print(date_invoice)
                    else:
                        date_invoice = False

                    customer_obj = self.env['res.partner'].search([('name', '=', customer)])
                    # user_obj = self.env['res.users'].search([('name', '=', user)])
                    product_obj = self.env['product.template'].search([('name', '=', product)])
                    # journal_obj = self.env['account.journal'].search([('name', '=', 'Customer Invoices')])
                    # account_type_id = self.env['account.account.type'].search([('name', '=', 'Income')])
                    account_id = self.env['account.account'].search([('code','=',200000)])
                    # uom = self.env['product.uom'].search([('name', '=', product_obj.uom_id.name)])
                    # so_obj = self.env['sale.order'].search([('source_no', '=', so_source)])

                    if customer:
                        invoice_vals = {
                            'partner_id': customer_obj.id,
                            # 'payment_term_id': 1,
                            'date_invoice': date_invoice,
                            'type':'out_invoice',
                            # 'date_due': due_date,
                            # 'user_id': user_obj.id,
                            # 'team_id': 1,
                            # 'journal_id': journal_obj.id,
                            'account_id': account_id.id,
                            # 'invoice_number': inv_no,
                            # 'origin': so_source

                        }
                        invoice_id = self.env['account.invoice'].create(invoice_vals)
                        pri_unit = float(row[3].split('$')[1].split('/')[0])
                        qua = row[3].split(' -')[1].split(' hr')[0]
                        str2 = float(qua.replace(':', '.'))
                        inv_line_vals = {
                            'invoice_id': invoice_id.id,
                            'name': row[3].strip(),
                            'product_id': product_obj.id,
                            'quantity': str2,
                            'price_unit': pri_unit,
                            # 'invoice_line_tax_ids': [(4, 1)],
                            'account_id': account_id.id,
                            'price_subtotal': row[9].strip(),
                            # 'uom_id': uom.id
                        }
                        invoice_line_ids = self.env['account.invoice.line'].create(inv_line_vals)
                        cust_invoice_numbers = invoice_id
                        # invoice_status = {
                        #     'so_source': row[8].strip(),
                        #     'invoice_number': inv_no,
                        #     'invoice_state': row[13].strip()}
                        # invocie_list.append(invoice_status)

                    else:
                        inv_line_vals = {
                            'invoice_id': cust_invoice_numbers.id,
                            'name': row[3].strip(),
                            'product_id': product_obj.id,
                            'quantity': '01',
                            'price_unit':row[9].strip() ,
                            # 'invoice_line_tax_ids': [(4, 1)],
                            'account_id': account_id.id,
                            'price_subtotal': row[9].strip(),
                            # 'uom_id': uom.id
                        }
                        # invoice_line_ids = self.env['account.invoice.line'].create(inv_line_vals)
                        # _logger.error('------------error log_id exception---------- %s',cust_invoice_numbers )
                        self.env['account.invoice.line'].create(inv_line_vals)



            except Exception as e:
             _logger.info('error=====exception============ %s', e)
             row.append(rownum)
             faulty_rows.append(row)

            rownum += 1

class SupplierUploadCSV(models.TransientModel):
    _name = 'supplier.upload.csv'
    _description = "Supplier upload csv"

    file_upload = fields.Binary(string="File")


    @api.multi
    def supplier_invoice_upload_csv(self):
        csv_datas = self.file_upload
        print("fileeeeeeeee", csv_datas)
        fileobj = TemporaryFile('wb+')
        csv_datas = base64.decodestring(csv_datas)
        fileobj.write(csv_datas)
        fileobj.seek(0)
        str_csv_data = fileobj.read().decode('utf-8')
        lis = csv.reader(StringIO(str_csv_data), delimiter=',')
        print("lisssssssssssssss", lis)
        rownum = 0
        faulty_rows = []
        header = ''
        cust_invoice_numbers = {}
        invocie_list = []
        for row in lis:
            invoice_status = {}
            # contract_vals ={}
            try:
                if rownum == 0:
                    header = row
                else:
                    if not row:
                        continue
                    _logger.error('------------rownum---------- %s', rownum)

                    # inv_no = row[1].strip()
                    supplier = row[5].strip()
                    product = row[2].strip()
                    inv_date = row[0].strip()
                    # str5=inv_date +'00.00.00'
                    # print(str5)
                    # due_date = row[2].strip()
                    # so_source = row[6].strip()
                    # user =row[3].strip()
                    # name_des = row[3].split(' -')[0]
                    # pri_unit = float(row[3].split('$')[1].split('/')[0])
                    # qua = row[3].split(' -')[1].split(' hr')[0]
                    # quantity_unit = float(qua.replace(':', '.'))

                    if inv_date:
                        date_invoice = datetime.strptime(inv_date, '%b %d, %Y').strftime('%Y-%m-%d')
                        print(date_invoice)
                    else:
                        date_invoice = False

                    supplier_obj = self.env['res.partner'].search([('name', '=', supplier)])
                    # user_obj = self.env['res.users'].search([('name', '=', user)])
                    product_obj = self.env['product.template'].search([('name', '=', product)])
                    # journal_obj = self.env['account.journal'].search([('name', '=', 'Customer Invoices')])
                    # account_type_id = self.env['account.account.type'].search([('name', '=', 'Income')])
                    account_id = self.env['account.account'].search([('code', '=', 200000)])
                    # uom = self.env['product.uom'].search([('name', '=', product_obj.uom_id.name)])
                    # so_obj = self.env['sale.order'].search([('source_no', '=', so_source)])

                    if supplier:
                        invoice_vals = {
                            'partner_id': supplier_obj.id,
                            # 'payment_term_id': 1,
                            'date_invoice': date_invoice,
                            'type':'in_invoice',
                            # 'date_due': due_date,
                            # 'user_id': user_obj.id,
                            # 'team_id': 1,
                            # 'journal_id': journal_obj.id,
                            'account_id': account_id.id,
                            # 'invoice_number': inv_no,
                            # 'origin': so_source

                        }
                        invoice_id = self.env['account.invoice'].create(invoice_vals)
                        pri_unit = float(row[3].split('$')[1].split('/')[0])
                        qua = row[3].split(' -')[1].split(' hr')[0]
                        quantity_unit = float(qua.replace(':', '.'))
                        inv_line_vals = {
                            'invoice_id': invoice_id.id,
                            'name': row[3].strip(),
                            'product_id': product_obj.id,
                            'quantity': quantity_unit,
                            'price_unit': pri_unit,
                            # 'invoice_line_tax_ids': [(4, 1)],
                            'account_id': account_id.id,
                            'price_subtotal': row[9].strip(),
                            # 'uom_id': uom.id
                        }
                        invoice_line_ids = self.env['account.invoice.line'].create(inv_line_vals)
                        cust_invoice_numbers = invoice_id
                        # invoice_status = {
                        #     'so_source': row[8].strip(),
                        #     'invoice_number': inv_no,
                        #     'invoice_state': row[13].strip()}
                        # invocie_list.append(invoice_status)

                    else:
                        inv_line_vals = {
                            'invoice_id': cust_invoice_numbers.id,
                            'name': row[3].strip(),
                            'product_id': product_obj.id,
                            'quantity': '01',
                            'price_unit': row[9].strip(),
                            # 'invoice_line_tax_ids': [(4, 1)],
                            'account_id': account_id.id,
                            'price_subtotal': row[9].strip(),
                            # 'uom_id': uom.id
                        }
                        # invoice_line_ids = self.env['account.invoice.line'].create(inv_line_vals)
                        # _logger.error('------------error log_id exception---------- %s',cust_invoice_numbers )
                        self.env['account.invoice.line'].create(inv_line_vals)



            except Exception as e:
                _logger.info('error=====exception============ %s', e)
                row.append(rownum)
                faulty_rows.append(row)

            rownum += 1