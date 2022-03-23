# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    upwork_invoice = fields.Many2one('upwork.invoice', string='Upwork Invoice')
