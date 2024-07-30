# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class BudgetAnalysis(models.Model):
    _name = 'budget.analysis'
    _auto = False
    _description = 'Budget Analysis'

    planning_date = fields.Date('Planning Date')
    realization_date = fields.Date('Realization Date')
    category_id = fields.Many2one('budget.category')
    planning_id = fields.Many2one('budget.planning', string='Budget Planning')
    planning_line_id = fields.Many2one('budget.planning.line', string='Planning Items')
    realization_amount = fields.Float()
    planned_amount = fields.Float()
    difference = fields.Float()

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE OR REPLACE VIEW %s AS (
            SELECT
                max(brl.id) AS id,
				bp.id as planning_id,
                bpl.id as planning_line_id,
                bpl.amount as planned_amount,
                coalesce(sum(brl.amount), 0) as realization_amount,
                bpl.amount - coalesce(sum(brl.amount), 0) as difference,
                bpl.category_id as category_id,
                br.date as realization_date,
                bp.effective_date as planning_date
            FROM 
                budget_realization_line brl
                LEFT JOIN budget_realization br on br.id = brl.realization_id
                LEFT JOIN budget_planning_line bpl on bpl.id = brl.budget_line_id
				LEFT JOIN budget_planning bp on bp.id = br.planning_id
                LEFT JOIN budget_category bc on bc.id = bpl.category_id

            WHERE br.state = 'done'

            GROUP BY bpl.id, br.date, bpl.category_id, bp.id
            ORDER BY br.date desc
        )
        """ % self._table)
