from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to trigger project analytics recomputation.
        Uses batch processing for better performance.
        """
        lines = super().create(vals_list)
        self._trigger_project_analytics_recompute(lines)
        return lines

    def write(self, vals):
        """
        Override write to trigger project analytics recomputation.
        Only triggers when relevant fields change.
        """
        result = super().write(vals)
        
        # Only trigger recompute if fields that affect project analytics changed
        if any(key in vals for key in ['analytic_distribution', 'price_subtotal', 'price_total', 'debit', 'credit', 'balance']):
            self._trigger_project_analytics_recompute(self)
        
        return result

    def unlink(self):
        """
        Override unlink to trigger project analytics recomputation.
        Captures project IDs before deletion.
        """
        # Trigger BEFORE deletion so we can still access the data
        self._trigger_project_analytics_recompute(self)
        return super().unlink()

    def _trigger_project_analytics_recompute(self, lines):
        """
        Trigger recomputation of project analytics when move lines with analytic distribution change.
        
        Optimizations:
        - Prefetching for performance
        - Batch processing in chunks
        - Error handling per batch
        - Deduplication of project IDs
        
        Args:
            lines: Recordset of account.move.line records that changed
        """
        if not lines:
            return

        project_ids = set()

        # Prefetch analytic_distribution for all lines at once
        try:
            lines_with_distribution = lines.filtered(lambda l: l.analytic_distribution)
            
            if not lines_with_distribution:
                return
            
            # Get project plan reference once
            try:
                project_plan = self.env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)
            except Exception as e:
                _logger.warning(f"Could not load project plan reference: {e}")
                return
            
            if not project_plan:
                _logger.debug("Project analytic plan not found - skipping recompute trigger")
                return

            # Collect all analytic account IDs from all lines
            analytic_account_ids = set()
            
            for line in lines_with_distribution:
                try:
                    for analytic_account_id_str in line.analytic_distribution.keys():
                        try:
                            analytic_account_id = int(analytic_account_id_str)
                            analytic_account_ids.add(analytic_account_id)
                        except (ValueError, TypeError):
                            continue
                except Exception as e:
                    _logger.warning(f"Error parsing analytic_distribution for line {line.id}: {e}")
                    continue

            if not analytic_account_ids:
                return

            # Batch-fetch all analytic accounts at once (performance optimization)
            analytic_accounts = self.env['account.analytic.account'].browse(list(analytic_account_ids))
            
            # Filter for project plan accounts only
            project_analytic_accounts = analytic_accounts.filtered(
                lambda a: a.exists() and a.plan_id == project_plan
            )

            if not project_analytic_accounts:
                return

            # Find all projects linked to these analytic accounts in one query
            projects = self.env['project.project'].search([
                '|',
                ('analytic_account_id', 'in', project_analytic_accounts.ids),
                ('account_id', 'in', project_analytic_accounts.ids)
            ])

            if not projects:
                return

            project_ids = set(projects.ids)

        except Exception as e:
            _logger.error(f"Error collecting projects for analytics recompute: {e}", exc_info=True)
            return

        # Batch process projects to avoid memory issues
        if project_ids:
            project_ids_list = list(project_ids)
            chunk_size = 50  # Process 50 projects at a time
            total_projects = len(project_ids_list)
            
            _logger.info(f"Triggering recompute for {total_projects} project(s) in {(total_projects + chunk_size - 1) // chunk_size} batch(es)")
            
            for i in range(0, total_projects, chunk_size):
                chunk = project_ids_list[i:i + chunk_size]
                chunk_projects = self.env['project.project'].browse(chunk)
                
                try:
                    # Recompute financial data for this batch
                    chunk_projects._compute_financial_data()
                    
                    # Commit after each batch to avoid locking issues
                    # and to ensure progress is saved even if later batches fail
                    if not self.env.context.get('defer_commit'):
                        self.env.cr.commit()
                    
                    _logger.info(f"Recomputed financial data for batch {(i // chunk_size) + 1}: {len(chunk_projects)} project(s)")
                    
                except Exception as e:
                    # Log error but continue with next batch
                    _logger.error(
                        f"Error recomputing financial data for batch {(i // chunk_size) + 1} "
                        f"(project IDs: {chunk}): {e}",
                        exc_info=True
                    )
                    # Rollback this batch but continue
                    if not self.env.context.get('defer_commit'):
                        self.env.cr.rollback()
                    continue