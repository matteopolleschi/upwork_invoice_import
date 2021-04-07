# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class UpworkInvoice(models.Model):
    _name = 'upwork.invoice'
    _description = "Upwork Invoice"
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
                'price_unit': abs(res.amount_converted),
            }
            record_line = {
                'type': 'in_invoice',
                'partner_id': partner,
                'date_invoice': res.invoice_date if bool(res.invoice_date) else None,
                'upwork_invoice': res.id
                'invoice_line_ids': [(0, 0, supplier_line)],
            }
            record = self.env['account.invoice'].create(record_line)
            record.action_invoice_open()
            #export_e_invoice = self.env['wizard.export.fatturapa'].exportFatturaPA()
            wizard = self.wizard_model.with_context({'active_ids': [invoice.id]}).create({})
            wizard.include_ddt_data = 'dati_trasporto'
            res = wizard.exportFatturaPA()

            wizard = self._get_export_wizard(invoice)
            action = wizard.exportFatturaPA()

            wizard = self.wizard_model.create({})
            return wizard.with_context({'active_ids': [invoice_id]}).exportFatturaPA()

        elif res.invoice_type == "Processing Fee":
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
                'price_unit': abs(res.amount_converted),
            }
            record_line = {
                'type': 'in_invoice',
                'partner_id': upwork_partner,
                'date_invoice': res.invoice_date if bool(res.invoice_date) else None,
                'upwork_invoice': res.id
                'invoice_line_ids': [(0, 0, supplier_line)],
            }
            record = self.env['account.invoice'].create(record_line)
            record.action_invoice_open()
            #export_e_invoice = self.env['wizard.export.fatturapa'].exportFatturaPA()

        return res
