from odoo import models, fields, api, _


class ProjectRefreshWizard(models.TransientModel):
    _name = 'project.refresh.wizard'
    _description = 'Project Financial Data Refresh Wizard'

    hourly_rate = fields.Float(
        string='Stundensatz (€)',
        default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param(
            'project_analytics.default_hourly_rate', '66.0'
        )),
        required=True,
        help='Hourly rate for calculating adjusted labor costs (Labor Costs Bereinigt).'
    )

    def action_refresh_financial_data(self):
        """
        Refresh financial data for selected projects with the specified hourly rate.
        """
        self.ensure_one()

        # Get active project IDs from context
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return {'type': 'ir.actions.act_window_close'}

        # Store the hourly rate in context for use in computation
        projects = self.env['project.project'].browse(active_ids)
        projects = projects.with_context(custom_hourly_rate=self.hourly_rate)

        # Trigger recomputation
        projects._compute_financial_data()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Financial Data Refreshed'),
                'message': f'Financial data has been recalculated for {len(projects)} project(s) with hourly rate of {self.hourly_rate}€.',
                'type': 'success',
                'sticky': False,
            }
        }
