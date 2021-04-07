# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from datetime import datetime
from io import StringIO
import xml.etree.ElementTree as ET
import base64
import csv

_logger = logging.getLogger(__name__)

try:
    from codicefiscale import build

except ImportError:
    _logger.warning(
        "codicefiscale library not found. "
        "If you plan to use it, please install the codicefiscale library"
        " from https://pypi.python.org/pypi/codicefiscale")


class UpworkInvoice(models.Model):
    _name = 'upwork.invoice'
    _description = "Upwork Invoice"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ref ID', required=True)
    date = fields.Char(string='Date')
    invoice_date = fields.Date(string='Invoice date', compute='_compute_date', store=True)
    invoice_type = fields.Selection(string="Type", selection=[('Processing Fee', 'Processing Fee'), ('Payment', 'Payment'), ('Hourly', 'Hourly')])
    description = fields.Text(string='Description')
    agency = fields.Many2one('res.partner', string='Agency')
    freelancer = fields.Many2one('res.partner', string='Freelancer')
    team = fields.Char(string='Team')
    account_name = fields.Char(string='Account name')
    po = fields.Char(string='PO')
    amount = fields.Monetary(string='Amount', currency_field='dollar_currency')
    amount_converted = fields.Monetary(string='Amount in Euro', currency_field='euro_currency', compute='_compute_amount', store=True)
    amount_local_currency = fields.Monetary(string='Amount in local currency', currency_field='euro_currency')
    dollar_currency = fields.Many2one('res.currency', string="Currency", default= lambda self : self.env['res.currency'].search([('name', '=', 'USD')]).id, readonly=True)
    euro_currency = fields.Many2one('res.currency', string="Currency", default= lambda self : self.env['res.currency'].search([('name', '=', 'EUR')]).id, readonly=True)
    balance = fields.Monetary(string='Balance', currency_field='dollar_currency')
    invoice_file = fields.Binary(string="Source Document")
    stage_id = fields.Many2one('upwork.invoice.stage', string='Stage', index=True, default=lambda s: s._get_default_stage_id(), group_expand='_read_group_stage_ids', track_visibility='onchange')
    in_progress = fields.Boolean(related='stage_id.in_progress')
    color = fields.Integer()

    def convertDate(self, DateString):
        if bool(DateString) != False :
            Datelist = DateString.split()
            month = Datelist[0]
            day = Datelist[1].strip(',')
            year = Datelist[2]
            DateConst = month + " " + day + " " + year
            DateResult = datetime.strptime(DateConst, '%b %d %Y').date()
        else: DateResult = DateString
        return DateResult

    @api.depends('date')
    def _compute_date(self):
        for record in self:
            record.invoice_date = self.convertDate(record.date)
    
    @api.depends('amount')
    def _compute_amount(self):
        for record in self:
            result = self.env['upwork.invoice.rate'].search([('rate_date', '=', record.invoice_date)])
            if bool(result):
                record.amount_converted = record.amount * result.rate
            else: record.amount_converted = 0.0

    def _get_default_stage_id(self):
        return self.env['upwork.invoice.stage'].search([], order='sequence', limit=1)
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.sudo().search([], order=order)

    @api.model
    def create(self, values):
        res = super(UpworkInvoice, self).create(values)
        partner = None
        upwork_partner = None
        if bool(res.freelancer):
            partner = res.freelancer.id
        if bool(res.agency):
            partner = res.agency.id
        
        if bool(self.env['res.partner'].search([('name', '=', 'Upwork')])):
            upwork_partner = self.env['res.partner'].search([('name', '=', 'Upwork')])
        else :
            generic_city = self.env['res.city.it.code.distinct'].search([('name', '=', 'MILANO')])
            generic_state = self.env['res.country.state'].search([('name', '=', 'Milano')])
            generic_country = self.env['res.country'].search([('name', '=', 'Italy')])
            national_code = self.env['wizard.compute.fc']._get_national_code(generic_city.name, generic_state.code, fields.Date.today())
            fiscal_code = build('Upwork', 'Upwork', fields.Date.today(), 'M', national_code)
            upwork_partner = self.env['res.partner'].create({
                'name': 'Upwork', 
                'company_type': 'company', 
                'supplier': True,
                'street': 'Generic freelancer address',
                'city': 'MILANO',
                'country_id': generic_country.id,
                'zip': '20019',
                'vat': 'BE0477472701',
                'fiscalcode': fiscal_code,
            })

        if res.invoice_type == "Hourly":
            tax = self.env['account.tax'].search([('name', '=', 'Iva al 22% (credito)')])
            journal = self.env['account.invoice']._default_journal().id
            product =  self.env['product.product'].create({
                'name': res.description,
                'type': 'service'
            })
            supplier_line = {
                'product_id': product.id,
                'name': product.name,
                'quantity': 1,
                'account_id': journal,
                'invoice_line_tax_ids': [(4, tax.id, 0)],
                'price_unit': abs(res.amount_converted),
            }
            record_line = {
                'type': 'in_invoice',
                'partner_id': partner,
                'date_invoice': res.invoice_date if bool(res.invoice_date) else None,
                'upwork_invoice': res.id,
                'invoice_line_ids': [(0, 0, supplier_line)],
            }
            record = self.env['account.invoice'].create(record_line)
            record.action_invoice_open()
            wizard = self.env['wizard.export.fatturapa'].create({})
            export_e_invoice = wizard.with_context({'active_ids': [record.id]}).exportFatturaPA()
        elif res.invoice_type == "Processing Fee":
            tax = self.env['account.tax'].search([('name', '=', 'Iva al 22% (credito)')])
            journal = self.env['account.invoice']._default_journal().id
            product =  self.env['product.product'].create({
                'name': res.description,
                'type': 'service'
            })
            supplier_line = {
                'product_id': product.id,
                'name': product.name,
                'quantity': 1,
                'account_id': journal,
                'invoice_line_tax_ids': [(4, tax.id, 0)],
                'price_unit': abs(res.amount_converted),
            }
            record_line = {
                'type': 'in_invoice',
                'partner_id': upwork_partner.id,
                'date_invoice': res.invoice_date if bool(res.invoice_date) else None,
                'upwork_invoice': res.id,
                'invoice_line_ids': [(0, 0, supplier_line)],
            }
            record = self.env['account.invoice'].create(record_line)
            record.action_invoice_open()
            wizard = self.env['wizard.export.fatturapa'].create({})
            export_e_invoice = wizard.with_context({'active_ids': [record.id]}).exportFatturaPA()
        
        return res

    def write(self, values):
        res = super(UpworkInvoice, self).write(values)
        account_invoice = self.env['account.invoice'].search([('upwork_invoice.id', '=', self.id)])
        account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=', account_invoice.id)])
        upwork = self.env['res.partner'].search([('name', '=', 'Upwork')])
        
        if bool(values.get('name')):
            account_invoice.write({'name': values.get('name')})
        if bool(values.get('freelancer')):
            account_invoice.write({'partner_id': values.get('freelancer')})
        if bool(values.get('agency')):
            account_invoice.write({'partner_id': values.get('agency')})
        if bool(values.get('invoice_date')):
            account_invoice.write({'date_invoice': values.get('invoice_date')})
        if bool(values.get('description')):
            account_invoice_line.write({'name': values.get('description')})
        if bool(values.get('amount_converted')):
            account_invoice_line.write({'price_unit': abs(values.get('amount_converted'))})

        return res


class UpworkInvoiceStage(models.Model):
    _name = 'upwork.invoice.stage'
    _description = "Upwork Invoice Stage"
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True)
    description = fields.Text()
    sequence = fields.Integer(default=1)
    in_progress = fields.Boolean(string='In Progress', default=True)
    fold = fields.Boolean(string='Folded in Kanban', help='This stage is folded in the kanban view when there are not records in that stage to display.')


class UpworkInvoiceImport(models.Model):
    _name = 'upwork.invoice.import'
    _description = "Upwork Invoice Import"
    
    invoice_files = fields.Many2many(comodel_name='ir.attachment', relation='class_ir_attachments_rel_upwork_invoice', column1='class_id', column2='attachment_id', string='Attachments')
    
    def splitFullName(self, FullName):
        if bool(FullName) != False :
            Namelist = FullName.split(" ", 1)
            StringResult = {'firstname': Namelist[0], 'lastname': Namelist[1]}
        else: StringResult = {'firstname': '', 'lastname': ''}
        return StringResult

    def import_file(self, invoice_file):
        csv_data = base64.b64decode(invoice_file.datas)
        data_file = StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.DictReader(data_file)
        file_reader.extend(csv_reader)
        agency = ""
        freelancer = ""
        for line in file_reader:
            if line['Agency'] != "":
                if self.env['res.partner'].search([('name', '=', line['Agency'])]):
                    agency = self.env['res.partner'].search([('name', '=', line['Agency'])])
                else :
                    # Update for fiscale code compute
                    generic_city = self.env['res.city.it.code.distinct'].search([('name', '=', 'MILANO')])
                    generic_state = self.env['res.country.state'].search([('name', '=', 'Milano')])
                    generic_country = self.env['res.country'].search([('name', '=', 'Italy')])
                    national_code = self.env['wizard.compute.fc']._get_national_code(generic_city.name, generic_state.code, fields.Date.today())
                    fiscal_code = build(line['Agency'], line['Agency'], fields.Date.today(), 'M', national_code)
                    agency = self.env['res.partner'].create({
                        'name': line['Agency'], 
                        'company_type': 'company', 
                        'supplier': True,
                        'street': 'Generic freelancer address',
                        'city': 'MILANO',
                        'country_id': generic_country.id,
                        'zip': '20019',
                        'vat': 'BE0477472701',
                        'fiscalcode': fiscal_code,
                    })

            if line['Freelancer'] != "":
                if self.env['res.partner'].search([('name', '=', line['Freelancer'])]):
                    freelancer = self.env['res.partner'].search([('name', '=', line['Freelancer'])])
                else :
                    # Update for fiscale code compute
                    name = self.splitFullName(line['Freelancer'])
                    generic_city = self.env['res.city.it.code.distinct'].search([('name', '=', 'MILANO')])
                    generic_state = self.env['res.country.state'].search([('name', '=', 'Milano')])
                    generic_country = self.env['res.country'].search([('name', '=', 'Italy')])
                    national_code = self.env['wizard.compute.fc']._get_national_code(generic_city.name, generic_state.code, fields.Date.today())
                    fiscal_code = build(name['lastname'], name['firstname'], fields.Date.today(), 'M', national_code)
                    freelancer = self.env['res.partner'].create({
                        'firstname': name['firstname'],
                        'lastname': name['lastname'],
                        'name': line['Freelancer'],
                        'company_type': 'person', 
                        'supplier': True,
                        'street': 'Generic freelancer address',
                        'city': 'MILANO',
                        'country_id': generic_country.id,
                        'zip': '20019',
                        'vat': 'BE0477472701',
                        'fiscalcode': fiscal_code,
                    })
            
            self.env['upwork.invoice'].create({
                'name': line['Ref ID'] if 'Ref ID' in line.keys() else 'Ref ID Missing', 
                'date': line['Date'] if 'Date' in line.keys() else '', 
                'invoice_type': line['Type'] if 'Type' in line.keys() else '',
                'description': line['Description'] if 'Description' in line.keys() else '',
                'agency': agency.id if bool(agency) == True else '',
                'freelancer': freelancer.id if bool(freelancer) == True else '',
                'team': line['Team'] if 'Team' in line.keys() else '',
                'account_name': line['Account Name'] if 'Account Name' in line.keys() else '',
                'po': line['PO'] if 'PO' in line.keys() else '',
                'amount': float(line['Amount']) if bool(line['Amount']) and 'Amount' in line.keys() else None,
                'amount_local_currency': float(line['Amount in local currency']) if bool(line['Amount in local currency']) and 'Amount in local currency' in line.keys() else None,
                'balance': float(line['Balance']) if bool(line['Balance']) and 'Balance' in line.keys() else None,
                'invoice_file': invoice_file,
                })

    def import_files(self):
        for record in self.invoice_files:
            self.import_file(record)
        
        return {'type': 'ir.actions.client','tag': 'reload'}


class UpworkInvoiceRate(models.Model):
    _name = 'upwork.invoice.rate'
    _description = "Currency Rate"
    _order = 'id'

    name = fields.Char(string='Date', required=True)
    rate_date = fields.Date(string='Rate date', compute='_compute_date', store=True)
    rate = fields.Monetary(string='Rate', currency_field='euro_currency')
    euro_currency = fields.Many2one('res.currency', string="Currency", default= lambda self : self.env['res.currency'].search([('name', '=', 'EUR')]).id, readonly=True)
    color = fields.Integer()

    def convertDate(self, DateString):
        if bool(DateString) != False :
            Datelist = DateString.split()
            month = Datelist[0]
            day = Datelist[1].strip(',')
            year = Datelist[2]
            DateConst = month + " " + day + " " + year
            DateResult = datetime.strptime(DateConst, '%b %d %Y').date()
        else: DateResult = DateString
        return DateResult

    @api.depends('name')
    def _compute_date(self):
        for record in self:
            record.rate_date = self.convertDate(record.name)


class UpworkInvoiceRateImport(models.Model):
    _name = 'upwork.invoice.rate.import'
    _description = "Currency Rate Import"
    
    rate_files = fields.Many2many(comodel_name='ir.attachment', relation='class_ir_attachments_rel_upwork_invoice_rate', column1='class_id', column2='attachment_id', string='Attachments')
    
    def import_file(self, rate_file):
        csv_data = base64.b64decode(rate_file.datas)
        data_file = StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.DictReader(data_file)
        file_reader.extend(csv_reader)
        for line in file_reader:            
            self.env['upwork.invoice.rate'].create({
                'name': line['Date'] if 'Date' in line.keys() else 'Missing Date', 
                'rate': float(line['Rate']) if bool(line['Rate']) and 'Rate' in line.keys() else None,
                })

    def import_files(self):
        for record in self.rate_files:
            self.import_file(record)
        
        return {'type': 'ir.actions.client','tag': 'reload'}


class UpworkInvoiceFatturapa(models.Model):
    _name = 'upwork.invoice.fatturapa'
    _description = "Electronic Invoice"
    _order = 'id'

    name = fields.Char(string='Name', required=True)
    attachment = fields.Binary(string='Attachments')

    def update_electronic_invoice(self):
        Fattura = self.env['fatturapa.attachment.out']
        #Upwork_invoice = self.env['upwork.invoice'].search(['upwork_invoice', '!=', False])
        tags = ['IdFiscaleIVA', 'CodiceFiscale', 'Sede']
        
        def iterator(parents, nested=False, tag=None):
            for child in parents:
                if nested:
                    if len(child) >= 1:
                        iterator(child, nested, tag)
                if child.tag == tag:
                    parents.remove(child)
        
        #for f_id in Fattura.search(['out_invoice_ids', 'in', Upwork_invoice]):
        for fatturapa in Fattura.search([]):
            xml_string = fatturapa.ir_attachment_id.get_xml_string()
            root = ET.fromstring(xml_string)
            for tag in tags:
                iterator(root, nested=True, tag=tag)
            xml_string = ET.tostring(root)
            xml_file_name = 'upwork_'+ fatturapa.name
            self.env['upwork.invoice.fatturapa'].create({
                'name': xml_file_name, 
                'attachment': base64.b64encode(xml_string), 
            })