from odoo import api,fields,models
import io
import base64
import xlsxwriter
from odoo.exceptions import ValidationError
from odoo.http import request, content_disposition

import logging
_logger = logging.getLogger(__name__)


class AccountTopCustomerVendorWizard(models.TransientModel):
    _name = "account.top.customer.vendor.wizard"
    _description = "Account Top Customer/Vendor Wizard For Printing Records"
        
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    #PERIOD
    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date",required=True)

    #CONFIGURATION
    invoice_status = fields.Selection([('all_invoices','All Invoices'),('draft','Draft'),('posted','Posted')],string="Invoice Status",default='all_invoices',required=True)

    type = fields.Selection([('top_customers','Top Customers'),('top_vendors','Top Vendors')],string="Type", default='top_customers')

    top_count = fields.Integer(string="Top Count", required=True)

    report_by = fields.Selection([('total_amount','Total Amount'),('total_order','Total Order'),('total_quantity','Total Quantity')],string="Report By", default='total_amount',required=True)

    # COMPARISON
    compare_with_previous_period = fields.Boolean(string="Compare with Previous Period?")

    comparison_from_date = fields.Date(string="Comparison From Date")
    
    comparison_to_date = fields.Date(string="Comparison To Date")

    def _format_report_date(self, date_value):
        date_value = fields.Date.to_date(date_value) if date_value else False
        return date_value.strftime('%d/%m/%Y') if date_value else ''
    
    def get_report_date(self):
        return fields.Datetime.context_timestamp(
            self,
            fields.Datetime.now()
        ).strftime('%d-%m-%Y_%H.%M.%S')
    
    #Condition for Top Count
    @api.constrains('top_count')
    def _check_top_count(self):
        for record in self:
            if record.top_count <= 0:
                raise ValidationError("Top Count must be greater than zero.")
            
    @api.depends('from_date', 'to_date', 'comparison_from_date', 'comparison_to_date', 'compare_with_previous_period')
    def date_validation(self):
        if self.from_date and self.to_date and self.to_date < self.from_date:
            raise ValidationError("To Date cannot be earlier than From Date.")
        
        if self.compare_with_previous_period:
            if self.comparison_from_date and self.comparison_to_date and self.comparison_to_date < self.comparison_from_date:
                raise ValidationError("Comparison To Date cannot be earlier than Comparison From Date.")
        

    def _validate_report_inputs(self):
        self.date_validation()

        if self.compare_with_previous_period:
            if not self.comparison_from_date:
                raise ValidationError("Please select Comparison From Date.")

            if not self.comparison_to_date:
                raise ValidationError("Please select Comparison To Date.")



    def _genrate_report_data(self):
            for rec in self:

                account_domain = []

                if rec.from_date:
                    account_domain.append(('date', '>=', rec.from_date))

                if rec.to_date:
                    account_domain.append(('date', '<=', rec.to_date))

                account_domain.append(('company_id', '=', self.company_id.id))

                # Invoice state filter
                if rec.invoice_status != 'all_invoices':
                    account_domain.append(('state', '=', rec.invoice_status))
                
                if rec.type == 'top_customers':
                    account_domain += [
                        ('move_type', '=', 'out_invoice'),
                        ('journal_id.type', '=', 'sale'),
                        ('partner_id', '!=', False),
                    ]

                else:
                    account_domain += [
                        ('move_type', '=', 'in_invoice'),
                        ('journal_id.type', '=', 'purchase'),
                        ('partner_id', '!=', False),
                    ]

                account_lines = rec.env['account.move'].search(account_domain)

                partner_data = {}

                for move in account_lines:

                    partner = move.partner_id

                    if partner.id not in partner_data:
                        partner_data[partner.id] = {
                            'partner_id': partner.id,
                            'partner_name': partner.display_name,
                            'total_amount': 0.0,
                            'invoice_count': 0,
                            'total_qty': 0.0,
                        }

                    partner_data[partner.id]['total_amount'] += move.amount_total
                    partner_data[partner.id]['invoice_count'] += 1

                    for line in move.invoice_line_ids.filtered(lambda l: l.product_id):
                                            
                        # Skip down payment lines
                        if 'Down payment' in (line.name or ''):
                            continue

                        qty = abs(line.quantity or 0.0)

                        partner_data[partner.id]['total_qty'] += qty  

                # Sort by total amount desc
                result = sorted(
                    partner_data.values(),
                    key=lambda x: x['total_amount'],
                    reverse=True
                )[:rec.top_count]

                return result

    def _get_comparison_data(self):

        """
        Logic: 
        - New: Partners with invoices in current period but NO invoices before.
        - Lost: Partners with invoices before but NO invoices in current period.
        """

        move_types = ['out_invoice']


        # Vendors
        if self.type == 'top_vendors':
            move_types = ['in_invoice']
            
        domain_current = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('move_type', 'in', move_types),
        ]

        domain_before = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.comparison_from_date),
            ('date', '<=', self.comparison_to_date),
            ('move_type', 'in', move_types),
        ]

        current_partners = self.env['account.move'].search(domain_current).mapped('partner_id')
        past_partners = self.env['account.move'].search(domain_before).mapped('partner_id')

        new_partners = current_partners - past_partners
        lost_partners = past_partners - current_partners

        return {
            'new_partners': new_partners,
            'lost_partners': lost_partners,
        }
        

    def report_pdf(self):

        self._validate_report_inputs()
        
        return self.env.ref("pf_top_invoice_bils.action_report_top_customer_vendor_pdf").report_action(self)



    def report_xls(self):
        self._validate_report_inputs()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/pf_top_invoice_bils/download_xlsx/{self.id}',
            'target': 'self',
        }

    def generate_xlsx_file(self):
        
        self._validate_report_inputs()

        # 1. Fetch dynamic data
        report_lines = self._genrate_report_data()
        comparison_data = self._get_comparison_data()

        period_str = f"{self._format_report_date(self.from_date)} to {self._format_report_date(self.to_date)}"

        compare_period_str = (
            f"{self._format_report_date(self.comparison_from_date)} to {self._format_report_date(self.comparison_to_date)}"
            if self.compare_with_previous_period else "N/A"
        )

        report_title = "Top Customers" if self.type == 'top_customers' else "Top Vendors"

        # 2. Setup Workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet_name = "Top Customers" if self.type == 'top_customers' else "Top Vendors"
        worksheet = workbook.add_worksheet(worksheet_name)

        # 3. Define Formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3',
            'border': 1
        })

        label_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D3D3D3'
        })

        base_border = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'            
        })

        num_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'center'
        })

        center_border = workbook.add_format({
            'border': 1,
            'align': 'center'
        })

        no_data_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1
        })
        rank_border = workbook.add_format({
            'border': 1,
            'align': 'right',
        })

        # Set Column Widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 25)

        # --- HEADER ---
        worksheet.merge_range('A1:C1', report_title, header_format)

        # --- PERIOD ROW ---
        worksheet.write('A2', "Period:", label_format)
        worksheet.merge_range('B2:C2', period_str, base_border)

        # --- TABLE HEADERS ---
        if self.report_by == 'total_amount':
            third_header = "Total Amount"
        elif self.report_by == 'total_order':
            third_header = "Total Orders"
        elif self.report_by == "total_quantity":
            third_header = "Total Quantity"

        headers = ["Rank", "Partner", third_header]

        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)

        # --- DYNAMIC DATA ---
        current_row = 4
        rank = 1

        if report_lines:

            for line in report_lines:

                value = 0.0

                if self.report_by == 'total_amount':
                    value = line.get('total_amount', 0.0)

                elif self.report_by == 'total_order':
                    value = line.get('invoice_count', 0)

                elif self.report_by == 'total_quantity':
                    value = line.get('total_qty', 0.0)

                worksheet.write(current_row, 0, rank, rank_border)
                worksheet.write(current_row, 1, line.get('partner_name', ''), base_border)

                if self.report_by == 'total_amount':
                    worksheet.write(current_row, 2, value, num_format)
                else:
                    worksheet.write(current_row, 2, value, center_border)

                current_row += 1
                rank += 1

        else:
            worksheet.merge_range(
                current_row,
                0,
                current_row,
                2,
                "No partner available for the selected period.",
                no_data_format
            )
            current_row += 1

        # Spacer
        current_row += 2

        # --- COMPARISON SECTION ---
        if self.compare_with_previous_period:

            worksheet.merge_range(
                current_row,
                0,
                current_row,
                2,
                f"Comparison Period: {compare_period_str}",
                header_format
            )
            current_row += 1

            new_label = "New Customers" if self.type == 'top_customers' else "New Vendors"
            lost_label = "Lost Customers" if self.type == 'top_customers' else "Lost Vendors"

            worksheet.write(current_row, 0, new_label, label_format)
            worksheet.write(current_row, 1, lost_label, label_format)

            current_row += 1

            new_list = comparison_data.get('new_partners', [])
            lost_list = comparison_data.get('lost_partners', [])

            if not new_list and not lost_list:

                worksheet.merge_range(
                    current_row,
                    0,
                    current_row,
                    2,
                    "No comparison data available.",
                    no_data_format
                )

            else:

                max_len = max(len(new_list), len(lost_list))

                for i in range(max_len):

                    new_name = new_list[i].name if i < len(new_list) else ""
                    lost_name = lost_list[i].name if i < len(lost_list) else ""

                    worksheet.write(current_row + i, 0, new_name, base_border)
                    worksheet.write(current_row + i, 1, lost_name, base_border)

        # 4. Finalize Workbook
        workbook.close()

        output.seek(0)

        xlsx_data = output.read()

        report_by = (
            'By Order'
            if self.report_by == 'total_order'
            else ' By Quantity'
            if self.report_by in ['total_qty', 'total_quantity']
            else ' By Amount'
        )

        date_time = self.get_report_date()

        file_name = f'{report_title} {report_by}-{date_time}.xlsx'

        output.close()

        return request.make_response(
            xlsx_data,
            headers=[
                (
                    'Content-Type',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
                (
                    'Content-Disposition',
                    content_disposition(file_name)
                )
            ]
        )