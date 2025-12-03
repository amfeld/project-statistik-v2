from odoo import models, fields, api, _
import logging
import json

_logger = logging.getLogger(__name__)


class ProjectAnalytics(models.Model):
    _inherit = 'project.project'
    _description = _('Project Analytics Extension')

    client_name = fields.Char(
        string='Name of Client',
        related='partner_id.name',
        store=True,
        help="The customer/client this project is for. This is automatically filled from the project's partner."
    )
    head_of_project = fields.Char(
        string='Head of Project',
        related='user_id.name',
        store=True,
        help="The person responsible for managing this project. This is the project manager assigned to the project."
    )

    # Sequence for manual drag&drop sorting in list view
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Used for manual sorting in the project statistics list view. Lower numbers appear first."
    )

    # Data Availability Status
    has_analytic_account = fields.Boolean(
        string='Has Analytic Account',
        compute='_compute_financial_data',
        store=True,
        help="Indicates whether this project has a valid analytic account for financial tracking. If False, no financial data can be calculated."
    )
    data_availability_status = fields.Selection([
        ('available', 'Data Available'),
        ('no_analytic_account', 'No Analytic Account'),
    ], string='Data Status',
        compute='_compute_financial_data',
        store=True,
        help="Shows whether financial data is available for this project. 'No Analytic Account' means the project is not configured for financial tracking."
    )

    # Customer Invoice fields - NET (without tax)
    customer_invoiced_amount_net = fields.Float(
        string='Invoiced Amount (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount invoiced to customers (without VAT/tax). This is the base amount before taxes are added. Uses price_subtotal from invoice lines."
    )
    customer_paid_amount_net = fields.Float(
        string='Paid Amount (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount actually paid by customers (without VAT/tax). Calculated proportionally based on invoice payment status."
    )
    customer_outstanding_amount_net = fields.Float(
        string='Outstanding Amount (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount still owed by customers (without VAT/tax). This is Invoiced Net - Paid Net."
    )

    # Customer Invoice fields - GROSS (with tax)
    customer_invoiced_amount_gross = fields.Float(
        string='Invoiced Amount (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount invoiced to customers (with VAT/tax). This is the total amount including all taxes. Uses price_total from invoice lines."
    )
    customer_paid_amount_gross = fields.Float(
        string='Paid Amount (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount actually paid by customers (with VAT/tax). Calculated proportionally based on invoice payment status."
    )
    customer_outstanding_amount_gross = fields.Float(
        string='Outstanding Amount (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount still owed by customers (with VAT/tax). This is Invoiced Gross - Paid Gross."
    )

    # Vendor Bill fields - NET (without tax)
    vendor_bills_total_net = fields.Float(
        string='Vendor Bills (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Net amount of vendor bills (without VAT/tax). This is the base cost before taxes. Uses price_subtotal from bill lines."
    )

    # Vendor Bill fields - GROSS (with tax)
    vendor_bills_total_gross = fields.Float(
        string='Vendor Bills (Gross)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Gross amount of vendor bills (with VAT/tax). This is the total cost including all taxes. Uses price_total from bill lines."
    )

    # Skonto (Cash Discount) fields
    customer_skonto_taken = fields.Float(
        string='Customer Cash Discounts (Skonto)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Cash discounts granted to customers for early payment (Gewährte Skonti). This reduces project revenue. Calculated from expense accounts 7300-7303 and liability account 2130."
    )
    vendor_skonto_received = fields.Float(
        string='Vendor Cash Discounts Received',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Cash discounts received from vendors for early payment (Erhaltene Skonti). This reduces project costs and increases profit. Calculated from income accounts 4730-4733 and asset account 2670."
    )

    # Labor/Timesheet fields
    total_hours_booked = fields.Float(
        string='Total Hours Booked',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total hours logged in timesheets for this project (Gebuchte Stunden). This includes all timesheet entries from employees working on this project. Used to track resource utilization and calculate labor costs."
    )
    labor_costs = fields.Float(
        string='Labor Costs',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total cost of labor based on timesheets (Personalkosten). Calculated from timesheet entries multiplied by employee hourly rates. This is a major component of internal project costs. NET amount (no VAT on internal labor)."
    )
    total_hours_booked_adjusted = fields.Float(
        string='Total Hours Booked (Adjusted)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Adjusted total hours based on employee HFC (Hourly Forecast Correction) factors. Formula: sum(hours * employee.faktor_hfc). This provides a more accurate forecast of actual work effort by adjusting for employee efficiency factors."
    )
    labor_costs_adjusted = fields.Float(
        string='Labor Costs (Adjusted)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Adjusted labor costs calculated using general hourly rate from system parameters. Formula: total_hours_booked_adjusted * general_hourly_rate. Default rate is 66 EUR per hour. This provides standardized cost calculation across all employees."
    )

    # Other Cost fields
    other_costs_net = fields.Float(
        string='Other Costs (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Other internal costs excluding labor and vendor bills (net amount without VAT). These are miscellaneous project expenses tracked via analytic lines."
    )

    # Total Cost fields - NET (without tax)
    total_costs_net = fields.Float(
        string='Total Costs (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total internal project costs without tax (Nettokosten). Calculated as: Labor Costs + Other Costs (Net). Vendor bills are tracked separately. All amounts are NET (without VAT)."
    )

    # Summary fields - NET-based calculations
    profit_loss_net = fields.Float(
        string='Profit/Loss (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Project profitability based on NET amounts (Gewinn/Verlust Netto). Formula: (Invoiced Net - Customer Skonto) - (Vendor Bills Net - Vendor Skonto + Total Costs Net). Consistent NET-to-NET calculation for accurate accounting. A positive value indicates profit, negative indicates loss."
    )
    negative_difference_net = fields.Float(
        string='Losses (Net)',
        compute='_compute_financial_data',
        store=True,
        aggregator='sum',
        help="Total project losses as a positive number, NET basis (Verluste Netto). This shows the absolute value of negative profit/loss. If profit/loss is positive, this field is 0. Useful for tracking and reporting total losses."
    )

    @api.depends('partner_id', 'user_id')
    def _compute_financial_data(self):
        """
        Compute all financial data for the project based on analytic account lines.
        This is the single source of truth for Odoo v18 accounting.

        Uses the standard Odoo project analytic plan (analytic.analytic_plan_projects).

        IMPORTANT: This version calculates both NET (without tax) and GROSS (with tax) amounts
        for customer invoices and vendor bills. Profit/Loss is calculated on NET basis for
        accurate accounting (comparing apples to apples).

        Note: We depend on partner_id and user_id (guaranteed core fields) rather than
        account_id or sale_line_id which may not exist if certain modules aren't installed.
        The actual financial data is computed from account.analytic.line records.
        """
        for project in self:
            # Initialize all fields
            customer_invoiced_amount_net = 0.0
            customer_paid_amount_net = 0.0
            customer_outstanding_amount_net = 0.0
            customer_invoiced_amount_gross = 0.0
            customer_paid_amount_gross = 0.0
            customer_outstanding_amount_gross = 0.0

            vendor_bills_total_net = 0.0
            vendor_bills_total_gross = 0.0

            customer_skonto_taken = 0.0
            vendor_skonto_received = 0.0

            total_hours_booked = 0.0
            labor_costs = 0.0
            other_costs_net = 0.0
            total_costs_net = 0.0

            profit_loss_net = 0.0
            negative_difference_net = 0.0

            # Get the analytic account associated with the project (projects plan ONLY)
            analytic_account = None

            # Get the standard project analytic plan reference
            try:
                project_plan = self.env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)
            except Exception:
                project_plan = None

            if hasattr(project, 'analytic_account_id') and project.analytic_account_id:
                # Verify this is the project plan
                if project_plan and hasattr(project.analytic_account_id, 'plan_id') and project.analytic_account_id.plan_id == project_plan:
                    analytic_account = project.analytic_account_id

            # Fallback to account_id if analytic_account_id not found
            if not analytic_account and hasattr(project, 'account_id') and project.account_id:
                if project_plan and hasattr(project.account_id, 'plan_id') and project.account_id.plan_id == project_plan:
                    analytic_account = project.account_id

            if not analytic_account:
                _logger.warning(
                    f"Project '{project.name}' (ID: {project.id}) has no analytic account linked. "
                    f"Financial data cannot be calculated. Please ensure: "
                    f"1) Analytic Accounting is enabled in Accounting settings, "
                    f"2) This project has an analytic account assigned (Projects plan), "
                    f"3) Invoice/bill lines have analytic_distribution set."
                )
                # Set status fields
                project.has_analytic_account = False
                project.data_availability_status = 'no_analytic_account'

                # Set all fields to 0.0 (not -1.0) to indicate no data
                project.customer_invoiced_amount_net = 0.0
                project.customer_paid_amount_net = 0.0
                project.customer_outstanding_amount_net = 0.0
                project.customer_invoiced_amount_gross = 0.0
                project.customer_paid_amount_gross = 0.0
                project.customer_outstanding_amount_gross = 0.0
                project.vendor_bills_total_net = 0.0
                project.vendor_bills_total_gross = 0.0
                project.customer_skonto_taken = 0.0
                project.vendor_skonto_received = 0.0
                project.total_hours_booked = 0.0
                project.labor_costs = 0.0
                project.other_costs_net = 0.0
                project.total_costs_net = 0.0
                project.profit_loss_net = 0.0
                project.negative_difference_net = 0.0
                continue

            # 1. Calculate Customer Invoices (Revenue) - Both NET and GROSS
            customer_data = self._get_customer_invoices_from_analytic(analytic_account)
            customer_invoiced_amount_net = customer_data['invoiced_net']
            customer_paid_amount_net = customer_data['paid_net']
            customer_invoiced_amount_gross = customer_data['invoiced_gross']
            customer_paid_amount_gross = customer_data['paid_gross']

            # 2. Calculate Vendor Bills (Direct Costs) - Both NET and GROSS
            vendor_data = self._get_vendor_bills_from_analytic(analytic_account)
            vendor_bills_total_net = vendor_data['total_net']
            vendor_bills_total_gross = vendor_data['total_gross']

            # 3. Calculate Skonto (Cash Discounts) from analytic lines
            skonto_data = self._get_skonto_from_analytic(analytic_account)
            customer_skonto_taken = skonto_data['customer_skonto']
            vendor_skonto_received = skonto_data['vendor_skonto']

            # 4. Calculate Labor Costs (Timesheets) - NET amount
            timesheet_data = self._get_timesheet_costs(analytic_account)
            total_hours_booked = timesheet_data['hours']
            labor_costs = timesheet_data['costs']
            total_hours_booked_adjusted = timesheet_data['adjusted_hours']

            # 4a. Calculate Adjusted Labor Costs using general hourly rate from system parameters
            general_hourly_rate = float(
                self.env['ir.config_parameter'].sudo().get_param(
                    'project_statistic.general_hourly_rate', default='66.0'
                )
            )
            labor_costs_adjusted = total_hours_booked_adjusted * general_hourly_rate

            # 5. Calculate Other Costs (non-timesheet, non-bill analytic lines) - NET amount
            other_costs_net = self._get_other_costs_from_analytic(analytic_account)

            # 6. Calculate totals
            customer_outstanding_amount_net = customer_invoiced_amount_net - customer_paid_amount_net
            customer_outstanding_amount_gross = customer_invoiced_amount_gross - customer_paid_amount_gross

            total_costs_net = labor_costs + other_costs_net

            # 7. Calculate Profit/Loss - NET basis (consistent comparison)
            # Formula: (Revenue NET - Customer Skonto) - (Vendor Bills NET - Vendor Skonto + Internal Costs NET)
            # This ensures we're comparing NET revenue to NET costs (apples to apples)
            adjusted_revenue_net = customer_invoiced_amount_net - customer_skonto_taken
            adjusted_vendor_costs_net = vendor_bills_total_net - vendor_skonto_received
            profit_loss_net = adjusted_revenue_net - (adjusted_vendor_costs_net + total_costs_net)
            negative_difference_net = abs(min(0, profit_loss_net))

            # Update status fields (data available)
            project.has_analytic_account = True
            project.data_availability_status = 'available'

            # Update all computed fields
            project.customer_invoiced_amount_net = customer_invoiced_amount_net
            project.customer_paid_amount_net = customer_paid_amount_net
            project.customer_outstanding_amount_net = customer_outstanding_amount_net
            project.customer_invoiced_amount_gross = customer_invoiced_amount_gross
            project.customer_paid_amount_gross = customer_paid_amount_gross
            project.customer_outstanding_amount_gross = customer_outstanding_amount_gross

            project.vendor_bills_total_net = vendor_bills_total_net
            project.vendor_bills_total_gross = vendor_bills_total_gross

            project.customer_skonto_taken = customer_skonto_taken
            project.vendor_skonto_received = vendor_skonto_received

            project.total_hours_booked = total_hours_booked
            project.labor_costs = labor_costs
            project.total_hours_booked_adjusted = total_hours_booked_adjusted
            project.labor_costs_adjusted = labor_costs_adjusted
            project.other_costs_net = other_costs_net
            project.total_costs_net = total_costs_net

            project.profit_loss_net = profit_loss_net
            project.negative_difference_net = negative_difference_net

    def _get_customer_invoices_from_analytic(self, analytic_account):
        """
        Get customer invoices and credit notes via analytic_distribution in account.move.line.
        This is the Odoo v18 way to link invoices to projects.

        IMPORTANT: We calculate BOTH NET and GROSS amounts:
        - NET: price_subtotal (base amount without taxes)
        - GROSS: price_total (total amount including all taxes)

        We must calculate the project portion based on invoice LINE amounts,
        not full invoice amounts, because different lines may go to different projects.

        Handles both:
        - out_invoice: Customer invoices (positive revenue)
        - out_refund: Customer credit notes (negative revenue)

        Returns:
            dict: {
                'invoiced_net': float,
                'paid_net': float,
                'invoiced_gross': float,
                'paid_gross': float
            }
        """
        result = {
            'invoiced_net': 0.0,
            'paid_net': 0.0,
            'invoiced_gross': 0.0,
            'paid_gross': 0.0
        }

        # DEBUG: Log what we're searching for
        _logger.info(f"Searching for invoice lines for analytic account: {analytic_account.id} ({analytic_account.name})")

        # DIAGNOSTIC: Check each filter condition separately to find the issue
        all_move_lines = self.env['account.move.line'].search([])
        _logger.info(f"DIAGNOSTIC: Total move lines in database: {len(all_move_lines)}")

        customer_moves = self.env['account.move.line'].search([
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund'])
        ])
        _logger.info(f"DIAGNOSTIC: Customer invoice lines (any state): {len(customer_moves)}")

        posted_customer_moves = self.env['account.move.line'].search([
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund'])
        ])
        _logger.info(f"DIAGNOSTIC: Posted customer invoice lines: {len(posted_customer_moves)}")

        with_analytic = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund'])
        ])
        _logger.info(f"DIAGNOSTIC: Posted customer lines WITH analytic_distribution: {len(with_analytic)}")

        # Find all posted customer invoice/credit note lines with this analytic account
        # RELAXED FILTER: Removed account_type filter to catch all invoice lines
        # German accounting (SKR03/SKR04) might use different account types
        invoice_lines = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
            ('display_type', '=', False),  # Exclude section/note lines
        ])

        _logger.info(f"Found {len(invoice_lines)} potential invoice lines (before analytic filter)")

        matched_lines = 0
        for line in invoice_lines:
            if not line.analytic_distribution:
                continue

            # Skip reversal entries (Storno) - they cancel out the original entry
            if line.move_id.reversed_entry_id or line.move_id.reversal_move_id:
                continue

            # Parse the analytic_distribution JSON
            try:
                distribution = line.analytic_distribution
                if isinstance(distribution, str):
                    distribution = json.loads(distribution)

                # Check if this project's analytic account is in the distribution
                if str(analytic_account.id) in distribution:
                    matched_lines += 1
                    # Get the percentage allocated to this project for THIS LINE
                    percentage = distribution.get(str(analytic_account.id), 0.0) / 100.0

                    # Get the invoice to calculate payment proportion
                    invoice = line.move_id

                    # Calculate this line's contribution to the project
                    # NET: price_subtotal (without taxes)
                    line_amount_net = line.price_subtotal * percentage
                    # GROSS: price_total (with taxes)
                    line_amount_gross = line.price_total * percentage

                    # Credit notes (out_refund) reduce revenue, so subtract them
                    if invoice.move_type == 'out_refund':
                        line_amount_net = -abs(line_amount_net)  # Ensure negative
                        line_amount_gross = -abs(line_amount_gross)  # Ensure negative

                    result['invoiced_net'] += line_amount_net
                    result['invoiced_gross'] += line_amount_gross

                    _logger.info(f"  - Invoice {invoice.name}: NET={line_amount_net:.2f}, GROSS={line_amount_gross:.2f}, Account={line.account_id.code} ({line.account_id.account_type})")

                    # Calculate paid amount for this line
                    # Payment proportion = (invoice.amount_total - invoice.amount_residual) / invoice.amount_total
                    if abs(invoice.amount_total) > 0:
                        payment_ratio = (invoice.amount_total - invoice.amount_residual) / invoice.amount_total
                        line_paid_net = line_amount_net * payment_ratio
                        line_paid_gross = line_amount_gross * payment_ratio
                        result['paid_net'] += line_paid_net
                        result['paid_gross'] += line_paid_gross

            except Exception as e:
                _logger.warning(f"Error parsing analytic_distribution for line {line.id}: {e}")
                continue

        _logger.info(f"Matched {matched_lines} invoice lines for analytic account {analytic_account.id}")
        _logger.info(f"Result: NET invoiced={result['invoiced_net']:.2f}, GROSS invoiced={result['invoiced_gross']:.2f}")

        return result

    def _get_vendor_bills_from_analytic(self, analytic_account):
        """
        Get vendor bills and refunds via analytic_distribution in account.move.line.
        This is the Odoo v18 way to link bills to projects.

        IMPORTANT: We calculate BOTH NET and GROSS amounts:
        - NET: price_subtotal (base amount without taxes)
        - GROSS: price_total (total amount including all taxes)

        We must calculate the project portion based on bill LINE amounts,
        not full bill amounts, because different lines may go to different projects.

        Handles both:
        - in_invoice: Vendor bills (positive cost)
        - in_refund: Vendor refunds (negative cost)

        Returns:
            dict: {
                'total_net': float,
                'total_gross': float
            }
        """
        result = {
            'total_net': 0.0,
            'total_gross': 0.0
        }

        # DEBUG: Log what we're searching for
        _logger.info(f"Searching for vendor bill lines for analytic account: {analytic_account.id} ({analytic_account.name})")

        # DIAGNOSTIC: Check each filter condition separately to find the issue
        vendor_moves = self.env['account.move.line'].search([
            ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
        ])
        _logger.info(f"DIAGNOSTIC: Vendor bill lines (any state): {len(vendor_moves)}")

        posted_vendor_moves = self.env['account.move.line'].search([
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
        ])
        _logger.info(f"DIAGNOSTIC: Posted vendor bill lines: {len(posted_vendor_moves)}")

        vendor_with_analytic = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
        ])
        _logger.info(f"DIAGNOSTIC: Posted vendor lines WITH analytic_distribution: {len(vendor_with_analytic)}")

        # Find all posted vendor bill/refund lines with this analytic account
        # RELAXED FILTER: Removed account_type filter to catch all bill lines
        # German accounting (SKR03/SKR04) might use different account types
        bill_lines = self.env['account.move.line'].search([
            ('analytic_distribution', '!=', False),
            ('parent_state', '=', 'posted'),
            ('move_id.move_type', 'in', ['in_invoice', 'in_refund']),
            ('display_type', '=', False),  # Exclude section/note lines
        ])

        _logger.info(f"Found {len(bill_lines)} potential bill lines (before analytic filter)")

        matched_lines = 0
        for line in bill_lines:
            if not line.analytic_distribution:
                continue

            # Skip reversal entries (Storno) - they cancel out the original entry
            if line.move_id.reversed_entry_id or line.move_id.reversal_move_id:
                continue

            # Parse the analytic_distribution JSON
            try:
                distribution = line.analytic_distribution
                if isinstance(distribution, str):
                    distribution = json.loads(distribution)

                # Check if this project's analytic account is in the distribution
                if str(analytic_account.id) in distribution:
                    matched_lines += 1
                    # Get the percentage allocated to this project for THIS LINE
                    percentage = distribution.get(str(analytic_account.id), 0.0) / 100.0

                    # Get the bill to check type
                    bill = line.move_id

                    # Calculate this line's contribution to the project
                    # NET: price_subtotal (without taxes)
                    line_amount_net = line.price_subtotal * percentage
                    # GROSS: price_total (with taxes)
                    line_amount_gross = line.price_total * percentage

                    # Vendor refunds (in_refund) reduce costs, so subtract them
                    if bill.move_type == 'in_refund':
                        line_amount_net = -abs(line_amount_net)  # Ensure negative
                        line_amount_gross = -abs(line_amount_gross)  # Ensure negative

                    result['total_net'] += line_amount_net
                    result['total_gross'] += line_amount_gross

                    _logger.info(f"  - Bill {bill.name}: NET={line_amount_net:.2f}, GROSS={line_amount_gross:.2f}, Account={line.account_id.code} ({line.account_id.account_type})")

            except Exception as e:
                _logger.warning(f"Error parsing analytic_distribution for bill line {line.id}: {e}")
                continue

        _logger.info(f"Matched {matched_lines} bill lines for analytic account {analytic_account.id}")
        _logger.info(f"Result: NET bills={result['total_net']:.2f}, GROSS bills={result['total_gross']:.2f}")

        return result

    def _get_skonto_from_analytic(self, analytic_account):
        """
        Get Skonto (cash discounts) by querying analytic lines from discount accounts.

        This is a simpler and more reliable approach than analyzing reconciliation.
        Skonto entries are typically posted to specific accounts with analytic distribution.

        Customer Skonto (Gewährte Skonti):
        - Accounts 7300-7303 (expense - reduces profit)
        - Account 2130 (liability account for customer discounts)

        Vendor Skonto (Erhaltene Skonti):
        - Accounts 4730-4733 (income - increases profit)
        - Account 2670 (asset account for vendor discounts)

        Returns:
            dict: {'customer_skonto': amount, 'vendor_skonto': amount}
        """
        result = {'customer_skonto': 0.0, 'vendor_skonto': 0.0}

        # Get all analytic lines for this account
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', analytic_account.id)
        ])

        for line in analytic_lines:
            if not line.move_line_id or not line.move_line_id.account_id:
                continue

            account_code = line.move_line_id.account_id.code
            if not account_code:
                continue

            # Customer Skonto (Gewährte Skonti) - expense accounts 7300-7303 + liability 2130
            # These reduce our revenue/profit (customer got discount)
            if account_code.startswith(('7300', '7301', '7302', '7303', '2130')):
                result['customer_skonto'] += abs(line.amount)

            # Vendor Skonto (Erhaltene Skonti) - income accounts 4730-4733 + asset 2670
            # These increase our profit (we got discount from vendor)
            elif account_code.startswith(('4730', '4731', '4732', '4733', '2670')):
                result['vendor_skonto'] += abs(line.amount)

        return result

    def _get_timesheet_costs(self, analytic_account):
        """
        Get timesheet hours and costs from account.analytic.line.
        Timesheets have is_timesheet=True.

        Returns NET amounts (timesheets don't have VAT).
        Also calculates adjusted hours based on employee HFC factors.
        """
        result = {'hours': 0.0, 'costs': 0.0, 'adjusted_hours': 0.0}

        # Find all timesheet lines for this analytic account
        timesheet_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', analytic_account.id),
            ('is_timesheet', '=', True)
        ])

        for line in timesheet_lines:
            hours = line.unit_amount or 0.0
            result['hours'] += hours
            result['costs'] += abs(line.amount or 0.0)

            # Calculate adjusted hours using employee HFC factor
            if line.employee_id and hasattr(line.employee_id, 'faktor_hfc'):
                faktor_hfc = line.employee_id.faktor_hfc or 1.0
                result['adjusted_hours'] += hours * faktor_hfc
            else:
                # If no employee or no HFC factor, use 1.0 (no adjustment)
                result['adjusted_hours'] += hours

        return result

    def _get_other_costs_from_analytic(self, analytic_account):
        """
        Get other costs from analytic lines that are:
        - NOT timesheets (is_timesheet=False)
        - NOT from vendor bills (no move_line_id with in_invoice/in_refund)
        - Negative amounts (costs are negative in Odoo)

        Returns NET amounts.
        """
        other_costs = 0.0

        # Find all cost lines (negative amounts, not timesheets)
        cost_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', analytic_account.id),
            ('amount', '<', 0),
            ('is_timesheet', '=', False)
        ])

        for line in cost_lines:
            # Check if this line is NOT from a vendor bill
            is_from_vendor_bill = False
            if line.move_line_id:
                move = line.move_line_id.move_id
                if move and move.move_type in ['in_invoice', 'in_refund']:
                    is_from_vendor_bill = True

            # Only count if it's not from a vendor bill
            # (vendor bills are counted separately in vendor_bills_total)
            if not is_from_vendor_bill:
                other_costs += abs(line.amount)

        return other_costs

    def action_view_account_analytic_line(self):
        """
        Open analytic lines for this project with enhanced view showing NET amounts.
        Shows all account.analytic.line records associated with the project's analytic account.
        """
        self.ensure_one()

        # Get the analytic account
        analytic_account = None
        if hasattr(self, 'analytic_account_id') and self.analytic_account_id:
            analytic_account = self.analytic_account_id
        elif hasattr(self, 'account_id') and self.account_id:
            analytic_account = self.account_id

        if not analytic_account:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No analytic account found for this project.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Get the custom list view
        try:
            list_view = self.env.ref('project_statistic.view_account_analytic_line_list_enhanced')
            list_view_id = list_view.id
        except ValueError:
            list_view_id = False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Analytic Entries - %s') % self.name,
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form',
            'views': [(list_view_id, 'list'), (False, 'form')],
            'domain': [('account_id', '=', analytic_account.id)],
            'context': {'default_account_id': analytic_account.id},
            'target': 'current',
        }

    def action_open_project_dashboard(self):
        """
        Open the standard project dashboard/form view for this project.
        Called when clicking a row in the analytics list view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': False,  # Use default project form view
            'target': 'current',
        }

    def action_open_standard_project_form(self):
        """
        Open the standard Odoo project form view.
        Called from the analytics form view button.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': False,  # Use default project form view
            'target': 'current',
        }

    def action_open_analytics_form(self):
        """
        Open the project analytics form view.
        Called from the standard project form view button.
        """
        self.ensure_one()

        # Get the analytics form view ID
        try:
            analytics_form_view = self.env.ref('project_statistic.view_project_form_account_analytics')
            view_id = analytics_form_view.id
        except ValueError:
            _logger.error("Analytics form view not found: project_statistic.view_project_form_account_analytics")
            view_id = False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Financial Analysis - %s') % self.name,
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': dict(self.env.context, form_view_initial_mode='readonly'),
        }

    def action_refresh_financial_data(self):
        """
        Manually refresh/recompute all financial data for selected projects.
        This is useful when invoices or analytic lines are added/modified.
        Reloads the view after calculation to show updated values.
        """
        self._compute_financial_data()

        # Return a reload action with notification
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'notification': {
                    'title': _('Financial Data Refreshed'),
                    'message': _('Financial data has been recalculated for %s project(s).') % len(self),
                    'type': 'success',
                    'sticky': False,
                }
            }
        }
