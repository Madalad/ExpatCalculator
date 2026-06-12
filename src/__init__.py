"""ExpatCalculator core package — public API re-exports."""
from .calculator import TaxCalculator, project_investment
from .currency import fetch_currency_rates
from .formatters import print_comparison, print_tax_result
from .models import CostOfLivingBreakdown, InvestmentProjection, TaxBracket, TaxResult

__all__ = [
    "TaxCalculator",
    "project_investment",
    "fetch_currency_rates",
    "print_comparison",
    "print_tax_result",
    "CostOfLivingBreakdown",
    "InvestmentProjection",
    "TaxBracket",
    "TaxResult",
]
