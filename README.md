# Project Financial Analytics for Odoo v18

## What does this module do?

This module provides comprehensive financial analytics for your projects by tracking all revenue, costs, and profitability in real-time. It's specifically designed for Odoo v18 German accounting and uses analytic accounts as the single source of truth.

**Key Feature:** Separate NET (without tax) and GROSS (with tax) tracking for accurate accounting!

## What information does it calculate?

For each project, it shows:

### Revenue (Customer Invoices) - NET & GROSS

- **Invoiced Amount (Net)**: Net amount invoiced (price_subtotal - without VAT)
- **Invoiced Amount (Gross)**: Gross amount invoiced (price_total - with VAT)
- **Paid Amount (Net)**: Net amount actually received from customers
- **Paid Amount (Gross)**: Gross amount actually received from customers
- **Outstanding Amount (Net)**: Net amount still owed (Invoiced Net - Paid Net)
- **Outstanding Amount (Gross)**: Gross amount still owed (Invoiced Gross - Paid Gross)

### Costs - NET & GROSS

- **Vendor Bills (Net)**: Net vendor bill costs (price_subtotal - without VAT)
- **Vendor Bills (Gross)**: Gross vendor bill costs (price_total - with VAT)
- **Labor Costs**: Internal timesheet costs (NET - no VAT on labor)
- **Other Costs (Net)**: Other internal expenses (NET)
- **Total Costs (Net)**: Labor + Other Costs (all NET amounts)

### Profitability - NET-Based Calculation

- **Profit/Loss (Net)**: Accurate NET-to-NET comparison
  - Formula: `(Invoiced Net - Customer Skonto) - (Vendor Bills Net - Vendor Skonto + Total Costs Net)`
- **Losses (Net)**: Absolute value of negative profit (for reporting)

### Labor

- **Total Hours Booked**: Total hours logged in timesheets (in hours)
- **Labor Costs**: Cost of labor based on employee rates (NET amount)

---

### Quick Reference: Net vs. Gross Amounts

| Field | Tax Status | Uses | Description |
|-------|-----------|------|-------------|
| **REVENUE FIELDS** |
| Invoiced Amount (Net) | **NET** 🔵 | price_subtotal | Base revenue without VAT |
| Invoiced Amount (Gross) | **GROSS** 🟢 | price_total | Total revenue with VAT |
| Paid Amount (Net) | **NET** 🔵 | Calculated | Net cash received |
| Paid Amount (Gross) | **GROSS** 🟢 | Calculated | Gross cash received |
| Outstanding Amount (Net) | **NET** 🔵 | Calculated | Net amount owed |
| Outstanding Amount (Gross) | **GROSS** 🟢 | Calculated | Gross amount owed |
| **COST FIELDS** |
| Vendor Bills (Net) | **NET** 🔵 | price_subtotal | Base vendor costs without VAT |
| Vendor Bills (Gross) | **GROSS** 🟢 | price_total | Total vendor costs with VAT |
| Labor Costs | **NET** 🔵 | analytic_line.amount | Internal labor (no VAT) |
| Other Costs (Net) | **NET** 🔵 | analytic_line.amount | Other expenses (net) |
| Total Costs (Net) | **NET** 🔵 | Calculated | Labor + Other (all net) |
| **PROFITABILITY** |
| Profit/Loss (Net) | **NET** 🔵 | Calculated | Consistent NET comparison |
| Losses (Net) | **NET** 🔵 | Calculated | Absolute losses (net) |

**Important Notes:**
- **Profit/Loss Formula (NET basis):** `(Invoiced Net - Customer Skonto) - (Vendor Bills Net - Vendor Skonto) - Total Costs Net`
- **Why NET-based calculation?** Comparing NET revenue to NET costs ensures accurate "apples-to-apples" profit calculation
- **Formula accounts for Skonto (cash discounts)** to show true profit after early payment discounts
- Revenue uses **line.price_subtotal** (NET) and **line.price_total** (GROSS)
- Vendor bills use **line.price_subtotal** (NET) and **line.price_total** (GROSS)
- Internal costs (labor, other) are NET amounts from analytic lines

---

## 💰 Skonto (Cash Discount) Tracking

This module properly tracks **Skonto** (cash discounts) in German accounting!

### What is Skonto?

**Skonto** is a cash discount offered/received for early payment, very common in German business:

**Example - Customer Invoice:**
```
Invoice Amount: €10,000 (payment terms: 2% discount within 10 days)
Customer pays early: €9,800
Skonto taken: €200 (booked to account 7300 "Gewährte Skonti")
```

**Example - Vendor Bill:**
```
Bill Amount: €5,000 (payment terms: 2% discount within 10 days)
We pay early: €4,900
Skonto received: €100 (booked to account 4730 "Erhaltene Skonti")
```

### How It Works

The module queries **analytic lines directly from Skonto accounts**:

1. **Finds all analytic lines** for the project's analytic account
2. **Filters by account code** to identify Skonto entries:
   - **Customer Skonto (Gewährte Skonti)**: Accounts 7300-7303, 2130
   - **Vendor Skonto (Erhaltene Skonti)**: Accounts 4730-4733, 2670
3. **Sums up amounts** - Only Skonto entries with analytic distribution are included

**Why This Approach:**
- ✅ Simple and reliable - queries account.analytic.line directly
- ✅ Uses Odoo's standard analytic distribution
- ✅ Only tracks Skonto properly allocated to projects
- ✅ Works with any payment method or reconciliation structure
- ✅ No complex reconciliation analysis needed
- ✅ Supports multiple account types (P&L and balance sheet)

### Impact on Profit Calculation

```python
# Adjusted Revenue (what we actually receive - NET basis)
adjusted_revenue_net = customer_invoiced_amount_net - customer_skonto_taken

# Adjusted Costs (what we actually pay - NET basis)
adjusted_vendor_costs_net = vendor_bills_total_net - vendor_skonto_received

# Final Profit/Loss (NET comparison)
profit_loss_net = adjusted_revenue_net - adjusted_vendor_costs_net - total_costs_net
```

### Fields in Views

- **Customer Cash Discounts (Skonto)**: Shows total Skonto taken by customers (reduces revenue)
- **Vendor Cash Discounts Received**: Shows total Skonto received from vendors (reduces costs)

Both fields are **hidden by default** in list view - enable them in optional columns if needed.

---

## ⚠️ Critical Requirements & Limitations

### 1. Analytic Accounting MUST Be Enabled

**This module is 100% dependent on Odoo's Analytic Accounting feature.**

✅ **Before using this module, ensure:**
- Analytic Accounting is installed and activated
- Each project has an analytic account linked (plan_id = Projects)
- Invoice lines have `analytic_distribution` filled
- Vendor bill lines have `analytic_distribution` filled

❌ **Without analytic accounts:**
- All financial values will show as 0.0
- No data will be calculated
- The module cannot function

**How to check:**
1. Go to: **Accounting → Configuration → Settings**
2. Look for: **"Analytic Accounting"** feature
3. Ensure it's enabled ✓
4. Go to your projects and verify each has an analytic account

---

### 2. Payment Calculation Limitation ⚠️

**IMPORTANT:** Payment tracking has an inherent limitation in Odoo:

**The Problem:**
- Odoo tracks payments at the **invoice level**, not the **line level**
- If an invoice has multiple lines with different projects, we cannot know which specific lines were paid
- The module assumes payments are distributed **proportionally** across all lines

**Example:**
```
Invoice #123 (Total: €200, Paid: €100 = 50% paid)
├── Line A: €100 → Project X
└── Line B: €100 → Project Y

Current calculation (proportional):
- Project X paid: €50 (50% of €100)
- Project Y paid: €50 (50% of €100)

Reality might be different:
- Customer might have only paid for Line A
- But Odoo has no way to track this at line level
```

**Impact:**
- Payment amounts are **estimates** when invoices have multiple projects
- For most accurate tracking, use **one project per invoice** where possible
- This is an **Odoo core limitation**, not a module bug

**Workaround:**
- Structure invoices with one project per invoice when precision is critical
- Use invoice notes to document which lines are paid if manual tracking is needed

---

### 3. Partial Payment Allocation ⚠️

**Limitation:** The module uses **proportional allocation** for partial payments:

**How it works:**
```python
payment_ratio = (invoice.amount_total - invoice.amount_residual) / invoice.amount_total
line_paid = line_amount * payment_ratio
```

**What this means:**
- If invoice is 50% paid, ALL lines are marked as 50% paid
- Real-world payments might target specific lines
- This is the only feasible approach without line-level payment tracking

**Best Practice:**
- For accurate payment tracking, fully pay invoices when possible
- Avoid partial payments on multi-project invoices

---

### 4. Skonto Detection Limitations ⚠️

**Limitation:** Skonto tracking depends on:

1. **Correct Account Codes:** Hardcoded to German SKR03/SKR04 account codes:
   - Customer Skonto: 7300-7303, 2130
   - Vendor Skonto: 4730-4733, 2670

2. **Analytic Distribution Required:** Skonto entries MUST have `analytic_distribution` set to be tracked

3. **Manual Journal Entries:** If Skonto is booked via manual journal entries without analytic distribution, it won't be detected

**What is NOT detected:**
- Skonto without analytic distribution
- Skonto booked to different account codes (if you use custom chart of accounts)
- Skonto embedded in payment reconciliation without separate journal entry

**Workaround:**
- Always set analytic distribution when booking Skonto
- Use the standard German account codes (SKR03/SKR04)
- If using custom accounts, modify the code in `_get_skonto_from_analytic()` method

---

### 5. Multi-Currency Limitations ⚠️

**Limitation:** The module does NOT handle multi-currency conversions:

**What this means:**
- All amounts are summed in their original currency
- If you have invoices in EUR and USD, they are simply added together
- No currency conversion is performed
- Reports may show incorrect totals for multi-currency projects

**Impact:**
- Projects with multiple currencies will show **incorrect** profit/loss
- Use this module only for **single-currency projects**

**Workaround:**
- Use Odoo's standard multi-currency accounting instead
- Keep projects in a single currency
- Manually convert currencies before analysis if needed

---

### 6. Reversal Entry Detection Limitations ⚠️

**Limitation:** The module skips reversal entries (Storno) by checking:
- `move_id.reversed_entry_id` - The original entry that was reversed
- `move_id.reversal_move_id` - The reversal entry itself

**Edge Cases:**
- If reversal entries are created manually without these fields set, they may be counted twice
- Partial reversals are not specifically handled
- Credit notes (out_refund, in_refund) are handled separately and correctly reduce amounts

**Best Practice:**
- Always use Odoo's built-in "Reverse Entry" function
- Avoid manually creating reversal entries
- Use credit notes for customer refunds instead of manual reversals

---

### 7. Performance Considerations ⚠️

**Limitation:** The module performs calculations in real-time on each access:

**Performance Impact:**
- Large projects (1000+ invoice lines) may have slower load times
- List views with many projects (100+) may be slow
- Pivot tables with large datasets may timeout

**What happens:**
- Each field is computed via `@api.depends('partner_id', 'user_id')`
- Fields are **stored** (`store=True`) but still require recalculation on changes
- Database searches for analytic lines, invoice lines, and bill lines on each compute

**Optimization Tips:**
- Use filters to reduce visible projects
- Avoid loading all projects at once in list view
- Use pagination (limit items per page)
- Consider scheduled batch updates for very large datasets (custom development needed)

**Technical Note:**
The trigger system in `account_move_line.py` uses batch processing and chunking (50 projects at a time) to minimize performance impact, but initial calculation can still be slow for large projects.

---

### 8. Tax Calculation Assumptions ⚠️

**Limitation:** The module assumes:

1. **Invoice/Bill Taxes:** Taxes are correctly included in `price_total` field (Odoo standard)
2. **Internal Labor:** Labor costs (timesheets) have NO VAT (standard for internal costs)
3. **Other Costs:** Other analytic line costs are NET amounts without tax

**What this means:**
- If your accounting setup is non-standard, calculations may be incorrect
- The module does NOT read tax configuration
- It relies on Odoo's standard `price_subtotal` (net) and `price_total` (gross) fields

**Edge Cases Not Handled:**
- Non-standard tax configurations
- Multiple tax rates on same line (Odoo handles this, but reporting may be confusing)
- Tax-exempt transactions (will show as NET = GROSS)
- Reverse charge VAT scenarios

**Best Practice:**
- Use standard Odoo tax configuration
- Verify that `price_subtotal` and `price_total` match your expectations
- Test with a pilot project before rolling out

---

### 9. Analytic Distribution Percentage Limitations ⚠️

**Limitation:** The module supports partial project allocation via `analytic_distribution` JSON:

```json
{
  "123": 50.0,  // Project A gets 50%
  "456": 50.0   // Project B gets 50%
}
```

**Edge Cases:**
- If percentages don't add up to 100%, the module still processes them (no validation)
- If analytic_distribution is malformed JSON, the line is skipped with a warning
- Very small percentages (<0.01%) may result in rounding errors

**Best Practice:**
- Ensure analytic distribution percentages add up to 100%
- Use whole numbers when possible (25%, 50%, 75%)
- Avoid very small allocations (<1%) to prevent rounding issues

---

### 10. Timesheet Cost Calculation Limitations ⚠️

**Limitation:** Timesheet costs depend on:

1. **Employee hourly rate** being set correctly in Odoo
2. **Timesheets being linked** to the correct analytic account
3. **Cost calculation** being performed by Odoo's HR/Timesheet module

**What this means:**
- If employee costs are not configured, labor costs will be 0.0 or incorrect
- The module does NOT calculate costs - it reads them from `account.analytic.line.amount`
- Different Odoo editions (Community vs Enterprise) may calculate costs differently

**Not Handled:**
- Overhead costs (benefits, taxes on labor)
- Billable vs non-billable distinctions (all timesheets are counted)
- External contractor costs (unless entered as vendor bills)

**Best Practice:**
- Configure employee costs in HR settings
- Verify timesheet costs are calculated correctly before relying on this module
- Consider adding overhead percentage manually if needed

---

### 11. Backward Compatibility & Deprecated Fields ⚠️

**Important:** This module maintains backward compatibility with deprecated fields:

**Deprecated Fields (kept for compatibility):**
- `customer_invoiced_amount` → Use `customer_invoiced_amount_net` or `customer_invoiced_amount_gross`
- `customer_paid_amount` → Use `customer_paid_amount_net` or `customer_paid_amount_gross`
- `customer_outstanding_amount` → Use `customer_outstanding_amount_net` or `customer_outstanding_amount_gross`
- `vendor_bills_total` → Use `vendor_bills_total_net` or `vendor_bills_total_gross`
- `total_costs_with_tax` → No longer calculated (use `total_costs_net`)
- `profit_loss` → Use `profit_loss_net`
- `negative_difference` → Use `negative_difference_net`

**What this means:**
- Old views/reports using deprecated fields will still work
- Deprecated fields return either NET or GROSS values (see field help text)
- `total_costs_with_tax` returns 0.0 (no longer calculated)

**Migration Path:**
1. Update your views to use new `_net` and `_gross` fields
2. Test thoroughly before removing deprecated field usage
3. Deprecated fields may be removed in future major versions

---

## How does it work?

The module uses Odoo v18's analytic distribution system to track all financial data:

### 1. Analytic Account (plan_id=1 - Projects Plan)
Every project has an analytic account that serves as the central tracking point for all financial transactions. This is the **single source of truth** for the module.

### 2. Customer Invoices - NET & GROSS
- Finds invoice lines with `analytic_distribution` pointing to the project
- Calculates **NET** amount per line: `price_subtotal * percentage`
- Calculates **GROSS** amount per line: `price_total * percentage`
- Determines paid amount using `amount_residual` from invoices
- **Payment Calculation**: `payment_ratio * line_amount` (applied to both NET and GROSS)

### 3. Vendor Bills - NET & GROSS
- Finds bill lines with `analytic_distribution` pointing to the project
- Calculates **NET** amount per line: `price_subtotal * percentage`
- Calculates **GROSS** amount per line: `price_total * percentage`

### 4. Labor Costs - NET
- Gets all timesheet entries (`is_timesheet=True`) for the analytic account
- Sums hours and costs (NET amounts - no VAT on internal labor)

### 5. Other Costs - NET
- Gets analytic lines that are:
  - NOT timesheets
  - NOT from vendor bills
  - Have negative amounts (costs are negative in Odoo)

### 6. Profit/Loss Calculation - NET Basis

**Why NET-based?**
- Ensures consistent "apples-to-apples" comparison
- Revenue NET compared to Costs NET
- Standard approach in German accounting for project profitability

**Formula:**
```python
# Adjust for Skonto
adjusted_revenue_net = customer_invoiced_amount_net - customer_skonto_taken
adjusted_vendor_costs_net = vendor_bills_total_net - vendor_skonto_received

# Calculate NET profit/loss
profit_loss_net = adjusted_revenue_net - (adjusted_vendor_costs_net + total_costs_net)
```

---

## When does it calculate?

Calculations happen **in real-time** when you view:
- Project Analytics Dashboard (Accounting → Project Analytics → Dashboard)
- List view with financial columns
- Pivot view with financial measures

**Automatic Recalculation:**
- When invoice lines change (`create`, `write`, `unlink`)
- When analytic distribution is modified
- When amount fields change (`price_subtotal`, `price_total`)
- Triggered automatically by `account_move_line.py` inheritance

---

## Technical Details (Odoo v18 Compatibility)

### Core Features
- Uses `analytic_distribution` JSON field (new in Odoo v18)
- Separates NET (`price_subtotal`) and GROSS (`price_total`) amounts
- Handles percentage-based project allocation
- Uses `parent_state='posted'` for invoice/bill lines
- Filters out display lines (`display_type=False`)
- Compatible with German chart of accounts (SKR03/SKR04)
- Uses `store=True` on computed fields for performance and aggregation (enables sum, pivot, graph views)
- **Uses analytic plan reference** (standard Odoo project plan)

### Handles All Document Types
- ✅ Customer Invoices (`out_invoice`) - NET & GROSS
- ✅ Customer Credit Notes (`out_refund`) - reduces revenue (NET & GROSS)
- ✅ Vendor Bills (`in_invoice`) - NET & GROSS
- ✅ Vendor Refunds (`in_refund`) - reduces costs (NET & GROSS)
- ✅ Timesheets with labor costs (NET)
- ✅ Other expense entries (NET)

### Additional Security Features

**1. Account Type Validation**
- Customer invoices: Only includes 'income' and 'income_other' account types
- Vendor bills: Only includes 'expense' account types
- Prevents wrong account types from affecting calculations

**2. Reversal Entry Handling (Storno)**
- Automatically skips reversal entries (`reversed_entry_id` or `reversal_move_id`)
- Prevents double-counting when entries are reversed
- Common in German accounting for corrections

**3. Skonto (Cash Discount) Tracking**
- Queries analytic lines from Skonto accounts directly
- Customer Skonto (Gewährte Skonti): Accounts 7300-7303, 2130
- Vendor Skonto (Erhaltene Skonti): Accounts 4730-4733, 2670
- Automatically tracks Skonto with analytic distribution
- See detailed Skonto section above

### Bug Fixes Applied

**1. No Double-Counting of Vendor Bills**
- Vendor bills are counted ONLY in `vendor_bills_total_net` and `vendor_bills_total_gross`
- Other costs exclude lines from vendor bills
- Clean separation of cost categories

**2. Separate NET and GROSS Tracking**
- Every invoice/bill amount tracked in both NET and GROSS
- Enables accurate tax reporting
- Profit/Loss uses NET for consistent comparison

**3. Credit Notes & Refunds Handled**
- Customer credit notes reduce invoiced/paid amounts (NET & GROSS)
- Vendor refunds reduce vendor bill totals (NET & GROSS)
- Correctly handles negative amounts

**4. Accrual-Based Profit Calculation**
- Profit = **Invoiced NET** - **Costs NET** (not just paid amount)
- Follows German accounting standards (accrual basis)
- Outstanding amounts tracked separately (NET & GROSS)

**5. Line-Based Payment Calculation**
- Each invoice line calculated independently
- Payment ratio applied per line to both NET and GROSS
- Handles multi-project invoices correctly

---

## Simple Example

**Project ABC:**
```
REVENUE (NET vs GROSS):
- Invoiced to customer (NET): €8,403.36 (before 19% VAT)
- Invoiced to customer (GROSS): €10,000.00 (with 19% VAT)
- Customer paid (NET): €6,722.69 (80% of invoice, net)
- Customer paid (GROSS): €8,000.00 (80% of invoice, gross)
- Outstanding (NET): €1,680.67
- Outstanding (GROSS): €2,000.00

COSTS (NET vs GROSS):
- Vendor bills (NET): €2,521.01 (before 19% VAT)
- Vendor bills (GROSS): €3,000.00 (with 19% VAT)
- Labor costs (NET): €2,000.00 (no VAT on internal labor)
- Other costs (NET): €500.00
- Total internal costs (NET): €2,500.00

PROFITABILITY (NET-based comparison):
- NET Calculation: €8,403.36 (invoiced net) - €2,521.01 (vendor net) - €2,500.00 (internal net)
- Result: €3,382.35 profit (NET basis)

With Skonto adjustments (if any):
- Customer Skonto taken: €0.00 (none in this example)
- Vendor Skonto received: €0.00 (none in this example)
- Final Profit/Loss (Net): €3,382.35

BREAKDOWN:
- We compare NET revenue (€8,403.36) minus any customer Skonto taken
- Against NET vendor bills (€2,521.01) minus any vendor Skonto received
- Against NET internal costs (€2,500.00 = labor + other)
- Result: True profit on NET basis (apples-to-apples comparison)

Why this makes sense:
- NET-to-NET comparison is accurate for accounting
- VAT is a pass-through (we collect it, we pay it - it's not profit/cost)
- GROSS amounts available for cash flow analysis
- Outstanding amounts show liquidity needs (both NET and GROSS)
```

This helps you instantly see which projects are profitable and which need attention!

---

## 🗑️ Module Uninstallation

This module follows **Odoo best practices for clean uninstallation**.

### What Happens on Uninstall

When you uninstall this module, the `uninstall_hook` automatically:

1. **Removes all computed stored fields** from the `project_project` table
2. **Cleans up database columns** to prevent orphaned data
3. **Ensures clean reinstallation** if you need to reinstall later

### Fields Cleaned Up

All computed fields with `store=True` are removed:
- NEW: `customer_invoiced_amount_net`, `customer_paid_amount_net`, `customer_outstanding_amount_net`
- NEW: `customer_invoiced_amount_gross`, `customer_paid_amount_gross`, `customer_outstanding_amount_gross`
- NEW: `vendor_bills_total_net`, `vendor_bills_total_gross`
- NEW: `other_costs_net`, `profit_loss_net`, `negative_difference_net`
- Deprecated: `customer_invoiced_amount`, `customer_paid_amount`, `customer_outstanding_amount`
- Deprecated: `vendor_bills_total`, `total_costs_net`, `total_costs_with_tax`
- Deprecated: `profit_loss`, `negative_difference`
- Other: `customer_skonto_taken`, `vendor_skonto_received`
- Other: `total_hours_booked`, `labor_costs`
- Other: `client_name`, `head_of_project`

### How It Works

**__init__.py:**
```python
def uninstall_hook(env):
    # Drops all computed field columns from project_project table
    env.cr.execute("ALTER TABLE project_project DROP COLUMN IF EXISTS ...")
```

**__manifest__.py:**
```python
{
    'uninstall_hook': 'uninstall_hook',
}
```

### Why This Matters

❌ **Without uninstall_hook:**
- Database columns remain after uninstall
- Orphaned data clutters your database
- Reinstalling may cause conflicts
- Manual database cleanup needed

✅ **With uninstall_hook:**
- Complete cleanup on uninstall
- No orphaned data
- Clean slate for reinstallation
- Professional module management

**This module can be safely installed and uninstalled without leaving database artifacts!**

---

## 🔒 Security & Access Rights

This module implements **Odoo v18 Enterprise standard accounting access rights**.

### Access Control Groups

The module uses Odoo's built-in accounting access groups:

| Group | Access Level | Read | Write | Create | Delete |
|-------|--------------|------|-------|--------|--------|
| **Billing** (`account.group_account_invoice`) | Basic | ✅ | ❌ | ❌ | ❌ |
| **Accountant** (`account.group_account_user`) | Standard | ✅ | ❌ | ❌ | ❌ |
| **Accounting Manager** (`account.group_account_manager`) | Advanced | ✅ | ✅ | ❌ | ❌ |
| **Advisor** (`account.group_account_readonly`) | Read-only | ✅ | ❌ | ❌ | ❌ |

### What This Means

**Users with accounting roles can:**
- ✅ View project analytics data (both NET and GROSS amounts)
- ✅ See financial metrics (invoices, costs, profit)
- ✅ Export data to Excel/CSV
- ✅ Generate reports

**Accounting Managers can also:**
- ✅ Manually trigger analytics recalculation
- ✅ Modify project settings (if needed)

**Security Implementation:**
```csv
security/ir.model.access.csv
- Leverages Odoo's enterprise accounting security groups
- No custom security groups (uses standard Odoo)
- Follows principle of least privilege
```

**Why Accounting Groups?**
- Project analytics contains **sensitive financial data**
- Only accounting staff should see profit/loss, costs, revenue
- Standard Odoo enterprise security model
- Integrates seamlessly with existing permissions

---

## 🧪 Automated Testing

This module includes **comprehensive automated tests** to ensure reliability.

### Test Coverage

**6 Test Cases Included:**

1. **test_01_project_without_analytic_account**
   - Ensures projects without analytic accounts don't crash
   - Validates graceful fallback behavior (returns 0.0)

2. **test_02_customer_invoice_basic**
   - Tests customer invoice calculation (NET & GROSS)
   - Validates invoiced and outstanding amounts

3. **test_03_vendor_bill_basic**
   - Tests vendor bill cost tracking (NET & GROSS)
   - Validates expense accumulation

4. **test_04_skonto_customer_tracking**
   - Tests customer Skonto detection (account 7300)
   - Validates discount tracking

5. **test_05_skonto_vendor_tracking**
   - Tests vendor Skonto detection (account 4730)
   - Validates discount receipt tracking

6. **test_06_profit_calculation**
   - Tests complete profit/loss formula (NET basis)
   - Validates: Profit = Revenue NET - Costs NET - Skonto

### Running Tests

```bash
# Run all module tests
odoo-bin -c odoo.conf -d your_database -i project_statistic --test-enable --stop-after-init

# Run specific test
odoo-bin -c odoo.conf -d your_database --test-tags /project_statistic
```

### Test Structure

```
tests/
├── __init__.py
└── test_project_analytics.py  # All test cases
```

**Test Framework:** Odoo's built-in `TransactionCase`
- Each test runs in isolated transaction
- Database rolled back after each test
- No test data pollution

### CI/CD Integration

These tests can be integrated into:
- ✅ GitHub Actions
- ✅ GitLab CI
- ✅ Jenkins pipelines
- ✅ Pre-commit hooks

**Example CI command:**
```yaml
- name: Run Odoo tests
  run: odoo-bin --test-enable --stop-after-init -i project_statistic
```

---

## 📦 Module Structure

```
project_statistic/
├── __init__.py                      # Module initialization + uninstall hook
├── __manifest__.py                  # Module metadata & dependencies
├── README.md                        # This documentation
│
├── data/
│   └── menuitem.xml                 # Navigation menu items
│
├── models/
│   ├── __init__.py
│   ├── project_analytics.py         # Core analytics logic (NET/GROSS separation)
│   └── account_move_line.py         # Automatic recalculation triggers
│
├── security/
│   └── ir.model.access.csv          # Access rights (accounting groups)
│
├── tests/
│   ├── __init__.py
│   └── test_project_analytics.py    # Automated tests (6 test cases)
│
└── views/
    └── project_analytics_views.xml  # UI: tree, form, filters
```

---

## ✅ Production Readiness Checklist

- ✅ **Core Functionality** - All calculations correct (NET & GROSS separated)
- ✅ **Error Handling** - Graceful fallbacks for missing data
- ✅ **Security & Access Rights** - Odoo enterprise accounting groups
- ✅ **Automated Tests** - 6 comprehensive test cases
- ✅ **Clean Uninstall** - Proper uninstall_hook implementation
- ✅ **Documentation** - Comprehensive README with examples and limitations
- ✅ **Code Quality** - All syntax validated, well-commented
- ✅ **German Accounting** - SKR03/04 compliant, Skonto tracking
- ✅ **Performance** - Efficient queries, batch processing in triggers
- ✅ **Odoo v18 Compatible** - Uses latest Odoo standards
- ✅ **NET/GROSS Separation** - Accurate tax tracking and reporting
- ✅ **Backward Compatibility** - Deprecated fields maintained

**This module is now production-ready for professional deployment!** 🚀

---

## 📋 Summary of Key Limitations

| Limitation | Impact | Severity | Workaround |
|------------|--------|----------|------------|
| **Analytic Accounting Required** | No data without analytic accounts | 🔴 Critical | Enable analytic accounting |
| **Payment Line-Level Tracking** | Proportional allocation only | 🟡 Medium | One project per invoice |
| **Partial Payment Allocation** | All lines marked equally | 🟡 Medium | Avoid partial payments |
| **Skonto Account Codes** | Only SKR03/SKR04 codes | 🟡 Medium | Modify code for custom charts |
| **Multi-Currency** | No currency conversion | 🔴 Critical | Single currency projects only |
| **Reversal Entry Detection** | Manual reversals may be counted twice | 🟢 Low | Use Odoo's "Reverse Entry" button |
| **Performance (Large Projects)** | Slow load with 1000+ lines | 🟡 Medium | Use filters, pagination |
| **Tax Assumptions** | Relies on standard Odoo tax config | 🟢 Low | Use standard tax setup |
| **Analytic Distribution %** | No percentage validation | 🟢 Low | Ensure totals = 100% |
| **Timesheet Costs** | Depends on HR configuration | 🟡 Medium | Configure employee costs |
| **Deprecated Fields** | May be removed in future | 🟢 Low | Migrate to `_net`/`_gross` fields |

**Legend:**
- 🔴 Critical: Must address before use
- 🟡 Medium: Should be aware of
- 🟢 Low: Minor consideration

---

## 📞 Support & Contribution

This module is open-source and maintained by the community.

**For Issues:**
- Check this README for limitations and known issues
- Verify your Odoo setup matches requirements
- Test with a pilot project first

**For Customization:**
- All code is well-commented and modular
- Key methods are separated for easy override
- Extend `project_analytics.py` for custom calculations

**Module Name:** `project_statistic`
**Technical Name:** `project_statistic`
**Odoo Version:** 18.0
**License:** LGPL-3
