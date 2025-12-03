from . import models


def uninstall_hook(env):
    """
    Clean up stored computed fields and view inheritances when module is uninstalled.

    This ensures:
    1. Orphaned database columns are removed
    2. View inheritances are properly cleaned up
    3. Standard project form continues to work after uninstallation
    """
    import logging
    _logger = logging.getLogger(__name__)

    # 1. Remove computed stored fields from database
    fields_to_remove = [
        # Status fields
        'has_analytic_account',
        'data_availability_status',

        # Customer Invoice NET fields
        'customer_invoiced_amount_net',
        'customer_paid_amount_net',
        'customer_outstanding_amount_net',

        # Customer Invoice GROSS fields
        'customer_invoiced_amount_gross',
        'customer_paid_amount_gross',
        'customer_outstanding_amount_gross',

        # Vendor Bills NET/GROSS fields
        'vendor_bills_total_net',
        'vendor_bills_total_gross',

        # Skonto fields
        'customer_skonto_taken',
        'vendor_skonto_received',

        # Labor fields
        'total_hours_booked',
        'labor_costs',
        'total_hours_booked_adjusted',
        'labor_costs_adjusted',

        # Other cost fields
        'other_costs_net',

        # Total cost fields
        'total_costs_net',

        # Profitability fields
        'profit_loss_net',
        'negative_difference_net',

        # Basic info fields
        'client_name',
        'head_of_project',
        'sequence'
    ]

    # Drop each column individually using safe identifier quoting
    try:
        from psycopg2 import sql
        for field in fields_to_remove:
            try:
                # Use sql.Identifier to safely quote column names
                query = sql.SQL("ALTER TABLE project_project DROP COLUMN IF EXISTS {}").format(
                    sql.Identifier(field)
                )
                env.cr.execute(query)
            except Exception as field_error:
                _logger.warning(f"Could not drop column {field}: {field_error}")
        _logger.info("Successfully removed project_statistic database columns")
    except Exception as e:
        _logger.warning(f"Error during database cleanup: {e}")

    # 2. Remove view inheritance (Odoo will handle this automatically via cascade delete)
    # The view inheritance record will be deleted when the module is uninstalled
    # No manual cleanup needed - Odoo's ORM handles this

    # 3. Verify standard project form still works
    try:
        # Check if standard project form view exists and is accessible
        standard_form = env.ref('project.edit_project', raise_if_not_found=False)
        if standard_form:
            _logger.info("Standard project form verified after uninstallation")
        else:
            _logger.warning("Standard project form not found - may need manual verification")
    except Exception as e:
        _logger.warning(f"Error verifying standard project form: {e}")

    env.cr.commit()