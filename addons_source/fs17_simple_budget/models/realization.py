from odoo import _, api, fields, models

class BudgetRealization(models.Model):
    _name = 'budget.realization'
    _description = 'Budget Realization'
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(tracking=True)
    description = fields.Char(tracking=True)
    date = fields.Date(tracking=True, default=fields.Date.today())
    planning_id = fields.Many2one('budget.planning', string='Budget', tracking=True, ondelete='restrict')
    line_ids = fields.One2many('budget.realization.line', 'realization_id', string='Line')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, default='draft', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    total = fields.Monetary(compute='_compute_total', string='Total')
    
    @api.depends('line_ids')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(rec.line_ids.mapped('amount'))

    def name_get(self):
        return [(i.id, "%s (%s)" % (i.name, i.description)) for i in self]

    def button_submit(self):
        self.state = 'submit'
    
    def button_done(self):
        self.state = 'done'
        for line in self.line_ids:
            line.budget_line_id.is_active = not line.budget_line_id.remaining <= 0

    def button_draft(self):
        self.state = 'draft'
    
    def button_cancel(self):
        self.state = 'cancel'

    @api.onchange('date')
    def get_planning(self):
        avail_budget = self.env['budget.planning'].search([('effective_date', '<=', self.date), ('state','=','run')])
        domain = [('id','in',avail_budget.ids)]
        return {'domain': 
            {'planning_id': domain}
        }
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('budget.realization')
        return super(BudgetRealization, self).create(vals)


class BudgetRealizationLine(models.Model):
    _name = 'budget.realization.line'
    _description = 'Budget Realization Line'
    
    realization_id = fields.Many2one('budget.realization', string='Realization', ondelete='cascade')
    name = fields.Char('Description')
    budget_line_id = fields.Many2one('budget.planning.line', string='Budget', ondelete='restrict')
    amount = fields.Monetary('')
    planning_id = fields.Many2one('budget.planning', string='Planning', related='realization_id.planning_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)

    @api.onchange('budget_line_id')
    def _onchange_budget_line_id(self):
        if self.budget_line_id:
            if self.budget_line_id.category_id.consumed_all_budget:
                self.amount = self.budget_line_id.amount