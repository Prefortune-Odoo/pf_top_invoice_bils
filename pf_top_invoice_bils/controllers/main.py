import io

from odoo import http
from odoo.http import request, content_disposition
import xlsxwriter


class TopCustomerVendorXlsxController(http.Controller):

    @http.route(
        '/pf_top_invoice_bils/download_xlsx/<int:wizard_id>',
        type='http',
        auth='user'
    )
    def download_xlsx(self, wizard_id, **kwargs):

        wizard = request.env['account.top.customer.vendor.wizard'].browse(wizard_id)

        return wizard.generate_xlsx_file()