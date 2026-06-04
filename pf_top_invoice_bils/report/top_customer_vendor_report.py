from odoo import models


class ReportTopCustomerVendor(models.AbstractModel):
    _name = 'report.pf_top_invoice_bils.report_top_customer_vendor_pdf'
    _description = 'Top Customer Vendor Report'

    def _get_report_values(self, docids, data=None):

        docs = self.env['account.top.customer.vendor.wizard'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'account.top.customer.vendor.wizard',
            'docs': docs,
            'report_data': data.get('report_data', []) if data else [],
        }