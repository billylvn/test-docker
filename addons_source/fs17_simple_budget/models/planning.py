from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class BudgetPlanning(models.Model):
    _name = 'budget.planning'
    _description = 'Budget Planning'
    _order = 'effective_date desc'
    _rec_name = 'description'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Reference')
    description = fields.Char(tracking=True)
    active = fields.Boolean(default=True)
    effective_date = fields.Date('Effective Date', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id, tracking=True)
    planned_balance = fields.Monetary('Planned Balance', tracking=True, compute="_get_balance")
    total_income = fields.Monetary('Total Income', tracking=True, compute="_get_balance")
    difference = fields.Monetary('Difference', tracking=True, compute="_get_balance")
    ending_balance = fields.Monetary('Actual Balance', compute="_get_balance", tracking=True)
    consumed = fields.Float(compute='_get_balance', string='Consumed Percentage', tracking=True)
    consumed_balance = fields.Monetary(compute='_get_balance', string='Total Consumed', tracking=True)
    planned_expense_amount = fields.Monetary(compute='_get_balance', string='Planned Expense Amount')
    realization_expense_amount = fields.Monetary(compute='_get_balance', string='Realization Expense Amount')
    remaining_expense_amount = fields.Monetary(compute='_get_balance', string='Remaining Expense Amount')
    line_ids = fields.One2many('budget.planning.line', 'budget_id', string='Line', tracking=True, copy=True)
    realization_line_ids = fields.One2many('budget.realization.line', 'planning_id', string='Realization Line', domain=[('realization_id.state','=','done')])
    realization_ids = fields.One2many('budget.realization', 'planning_id', string='Realization')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('run', 'Running'),
        ('done', 'Closed'),
    ], string='Status', copy=False, default='draft', tracking=True)
    count_realization = fields.Integer(compute='_compute_count_realization', string='Count Realization')
    income_line_ids = fields.One2many('income.planning.line', 'budget_id', string='Income', copy=True)
    

    @api.depends('realization_ids')
    def _compute_count_realization(self):
        for rec in self:
            rec.count_realization = len(rec.realization_ids)

    def show_realization(self):
        return {
            'name': 'Budget Realization',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban,form' if self.count_realization >= 1 else 'form',
            'target': 'current',
            'domain': [('id','in',self.realization_ids.ids)],
            'res_model': 'budget.realization',
            'context': {'default_planning_id': self.id, 'create': self.state == 'run'}
        }

    def name_get(self):
        return [(i.id, "%s (%s)" % (i.name, i.description)) for i in self]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('budget.planning')
        return super(BudgetPlanning, self).create(vals)

    def button_draft(self):
        self.state = 'draft'

    def button_run(self):
        self.state = 'run'

    def button_lock(self):
        self.state = 'done'
        clearance_lines = []
        for line in self.line_ids.filtered(lambda x: x.remaining > 0):
            clearance_lines += [(0,0, {
                'name': 'Clearance',
                'budget_line_id': line.id,
                'amount': line.remaining
            })]
        if clearance_lines:
            clearance_realz = self.env['budget.realization'].create({
                'description': 'Clearance ' + self.description,
                'planning_id': self.id,
                'line_ids': clearance_lines
            })
            clearance_realz.button_done()

    @api.depends('line_ids','realization_line_ids', 'income_line_ids')
    def _get_balance(self):
        for rec in self:
            rec.planned_expense_amount = sum(rec.line_ids.mapped('amount'))
            rec.realization_expense_amount = sum(rec.realization_line_ids.mapped('amount'))
            rec.remaining_expense_amount = sum(rec.line_ids.mapped('remaining'))
            rec.planned_balance = sum(rec.income_line_ids.mapped('planned_amount')) - sum(rec.line_ids.mapped('amount'))
            rec.ending_balance = sum(rec.income_line_ids.mapped('realization_amount')) - sum(rec.realization_line_ids.filtered_domain([('realization_id.state','=','done')]).mapped('amount'))
            rec.difference = rec.ending_balance - rec.planned_balance
            rec.consumed_balance = sum(rec.realization_line_ids.mapped('amount'))
            rec.total_income = sum(rec.income_line_ids.mapped('realization_amount'))
            try:
                rec.consumed = (sum(rec.realization_line_ids.filtered_domain([('realization_id.state','=','done')]).mapped('amount')) /  sum(rec.income_line_ids.mapped('realization_amount'))) * 100
            except:
                rec.consumed = 0

class BudgetPlanningLine(models.Model):
    _name = 'budget.planning.line'
    _description = 'Budget Planning Line'
    _order = 'sequence asc'

    name = fields.Char('Description')
    sequence = fields.Integer('Sequence')
    category_id = fields.Many2one('budget.category', string='Category')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary('')
    budget_id = fields.Many2one('budget.planning', string='Budget', ondelete='cascade')
    realization_line_ids = fields.One2many('budget.realization.line', 'budget_line_id', string='Realization Line', domain=[('realization_id.state','in',['done', 'submit'])])
    realization = fields.Monetary(compute='_compute_realization', string='Realization', store=True)
    forecasted_amount = fields.Monetary(compute='_compute_realization', string='Realization', store=True)
    remaining = fields.Monetary('Remaining Amount', compute="_compute_realization", store=True)
    consumed = fields.Float('Consumed', compute="_compute_realization", store=True)
    is_active = fields.Boolean('Active', default=True)
    
    def show_realization(self):
        return {
            'name': 'Budget Realization - %s' % self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban,form',
            'target': 'current',
            'domain': [('id','in',self.realization_line_ids.ids)],
            'res_model': 'budget.realization.line',
            'context': {'create': False, 'edit': False, 'delete': False}
        }
    
    @api.depends('realization_line_ids', 'amount')
    def _compute_realization(self):
        for rec in self:
            rec.realization = sum(rec.realization_line_ids.filtered_domain([('realization_id.state','=','done')]).mapped('amount'))
            rec.remaining = rec.amount - rec.realization
            rec.forecasted_amount = rec.amount - sum(rec.realization_line_ids.mapped('amount'))
            try:
                rec.consumed = (rec.realization /  rec.amount) * 100
            except:
                rec.consumed = 0

    def name_get(self):
        return [(i.id, "%s %s" % (i.name, "("+i.category_id.name+")" if i.category_id else "")) for i in self]
    
class IncomePlanningLine(models.Model):
    _name = 'income.planning.line'
    _description = 'Income Planning Line'
    
    name = fields.Char('Description')
    category_id = fields.Many2one('income.category', string='Category')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    planned_amount = fields.Monetary('Planned Amount')
    realization_amount = fields.Monetary('Realization Amount')
    budget_id = fields.Many2one('budget.planning', string='Budget', ondelete='cascade')

    @api.onchange('planned_amount')
    def _onchange_planned_amount(self):
        if self.planned_amount:
            if not self.realization_amount:
                self.realization_amount = self.planned_amount

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id and not self.name:
            self.name = self.category_id.description