from odoo import _, api, fields, models

class BudgetCategory(models.Model):
    _name = 'budget.category'
    _description = 'Budget Category'
    
    name = fields.Char('')
    description = fields.Char('')
    consumed_all_budget = fields.Boolean('Consumed All Budget')

class IncomeCategory(models.Model):
    _name = 'income.category'
    _description = 'Income Category'
    
    name = fields.Char('')
    description = fields.Char('')