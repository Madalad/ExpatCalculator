"""
Command-line entry point for ExpatCalculator.

Run from the project root with:
    python -m src.script

This module also re-exports the public API, so existing imports keep working:
    from src.script import TaxCalculator, project_investment
"""
from .calculator import TaxCalculator, project_investment
from .currency import fetch_currency_rates
from .formatters import print_comparison, print_tax_result
from .models import CostOfLivingBreakdown, InvestmentProjection, TaxBracket, TaxResult

# ===== USER INPUT VARIABLES =====

# ANNUAL_INCOME: the annual income amount (currency determined by ANNUAL_INCOME_CURRENCY).
# Example: 100_000 for $100,000 or £100,000 depending on ANNUAL_INCOME_CURRENCY

# ANNUAL_INCOME_CURRENCY: the currency of the ANNUAL_INCOME input.
# Available options: "USD", "GBP"
# The income will be converted to USD, then to the local currency of LOCATION for tax calculations.

# LOCATION: location to calculate taxes and cost of living for.
# Available options: london, new_york, hong_kong, chicago, dubai, zurich, tokyo,
#                    singapore, toronto, sydney, amsterdam, cape_town, bern, bangkok

# LIFESTYLE: lifestyle level affecting cost of living estimates.
# Available options:
#   - "low":    Modest lifestyle (budget housing, public transport, local dining)
#   - "medium": Professional lifestyle (private housing, varied dining, entertainment)
#   - "high":   Luxury lifestyle (premium areas, fine dining, exclusive activities)

ANNUAL_INCOME = 100_000
ANNUAL_INCOME_CURRENCY = "USD"
LOCATION = "london"
LIFESTYLE = "medium"

# ================================


def main():
    calculator = TaxCalculator()

    tax_result = calculator.calculate_income_tax(ANNUAL_INCOME, ANNUAL_INCOME_CURRENCY, LOCATION)
    col_result = calculator.get_cost_of_living(LOCATION, LIFESTYLE)
    cap_gains_rate, notes = calculator.get_capital_gains_tax_rate(LOCATION)

    print_tax_result(tax_result, col_result, ANNUAL_INCOME_CURRENCY)
    print(f"\nCapital Gains Tax Rate:     {cap_gains_rate*100:.2f}%")
    print(f"Notes: {notes}")

    comparison = calculator.compare_locations(ANNUAL_INCOME, ANNUAL_INCOME_CURRENCY, LIFESTYLE)
    print_comparison(comparison, ANNUAL_INCOME_CURRENCY, ANNUAL_INCOME, LIFESTYLE)


if __name__ == "__main__":
    main()
