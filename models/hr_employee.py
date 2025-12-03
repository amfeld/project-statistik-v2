from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    faktor_hfc = fields.Float(
        string='Faktor HFC',
        default=1.0,
        help="Human Factor Coefficient - Used to adjust hours booked for this employee in project calculations. Default is 1.0 (100%)."
    )
