from openerp import api, fields, models, _


class UploadCSV(models.Model):
    _inherit = 'upload.csv'



    file_upload=fields.Binary(string="File")