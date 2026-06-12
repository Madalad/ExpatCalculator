"""Terminal output formatting for tax and comparison results."""
from .calculator import TaxCalculator
from .models import TaxResult, CostOfLivingBreakdown


def print_tax_result(result: TaxResult, col_result: CostOfLivingBreakdown = None, input_currency: str = "USD"):
    """Pretty print tax calculation result."""
    # Convert all monetary values from local currency to input currency
    input_to_usd = TaxCalculator.INPUT_CURRENCY_TO_USD[input_currency]
    to_input = 1 / (result.exchange_rate_usd * input_to_usd)

    gross       = result.gross_income        * to_input
    income_tax  = result.income_tax          * to_input
    social      = result.social_contributions * to_input
    total_tax   = result.total_tax           * to_input
    take_home   = result.take_home_pay       * to_input

    print(f"\n{'='*60}")
    print(f"Tax Calculation: {result.location}")
    print(f"{'='*60}")
    print(f"Gross Annual Income:        {gross:>12,.2f} {input_currency}")
    print(f"Income Tax:                 {income_tax:>12,.2f} {input_currency}")
    print(f"Social Contributions:       {social:>12,.2f} {input_currency}")
    print(f"Total Tax:                  {total_tax:>12,.2f} {input_currency}")
    print(f"Effective Tax Rate:         {result.effective_tax_rate*100:>12.2f}%")
    print(f"Take-Home Pay (Annual):     {take_home:>12,.2f} {input_currency}")
    print(f"Take-Home Pay (Monthly):    {take_home/12:>12,.2f} {input_currency}")

    if col_result:
        # Convert COL values to input currency
        input_to_usd = TaxCalculator.INPUT_CURRENCY_TO_USD[input_currency]
        housing_input = col_result.housing / input_to_usd
        food_input = col_result.food / input_to_usd
        transport_input = col_result.transport / input_to_usd
        utilities_input = col_result.utilities / input_to_usd
        other_input = col_result.other / input_to_usd
        annual_input = col_result.annual_total / input_to_usd
        monthly_input = col_result.monthly_total / input_to_usd

        # Get currency symbol
        currency_symbol = "$" if input_currency == "USD" else "£"

        s = currency_symbol
        print(f"\n{'Cost of Living Breakdown':^78}")
        print(f"  {'':20} {'Annual':>15} {'Monthly':>15}")
        print(f"  {'Housing':<20} {s}{housing_input:>14,.2f} {s}{housing_input/12:>14,.2f}")
        print(f"  {'Food':<20} {s}{food_input:>14,.2f} {s}{food_input/12:>14,.2f}")
        print(f"  {'Transport':<20} {s}{transport_input:>14,.2f} {s}{transport_input/12:>14,.2f}")
        print(f"  {'Utilities':<20} {s}{utilities_input:>14,.2f} {s}{utilities_input/12:>14,.2f}")
        print(f"  {'Other':<20} {s}{other_input:>14,.2f} {s}{other_input/12:>14,.2f}")
        print(f"  {'-'*46}")
        print(f"  {'Total':<20} {s}{annual_input:>14,.2f} {s}{monthly_input:>14,.2f}")


def print_comparison(comparison: dict, input_currency: str, annual_income: float, lifestyle: str):
    """Pretty print the cross-location comparison table."""
    print(f"\n{'COMPARISON ACROSS LOCATIONS':^60}")
    print(f"Income: {annual_income:,} {input_currency} | Lifestyle: {lifestyle}")
    print("="*60)

    # Sort by take-home pay in input currency (descending)
    sorted_comparison = sorted(
        comparison.items(),
        key=lambda x: x[1]["take_home_input"],
        reverse=True
    )

    # Get currency symbol
    currency_symbol = "$" if input_currency == "USD" else "£"

    # Print comparison table with organized columns (annual/monthly pairs together)
    print(f"\n{'Location':<22} {'Take-Home Pay':<23} {'Cost of Living':<29} Surplus")
    print(f"{'':11} {'Annual':>13} {'Monthly':>13} {'Annual':>11} {'Monthly':>11} {'Annual':>13} {'Monthly':>13} {'Eff. Tax Rate':>17} {'CG Tax Rate':>14}")
    print("-"*138)
    for loc, data in sorted_comparison:
        take_home_input = data["take_home_input"]
        col_annual_input = data["col_annual_input"]
        col_monthly_input = data["col_monthly_input"]
        annual_surplus = data["annual_surplus"]
        monthly_surplus = data["monthly_surplus"]
        tax_rate = data["tax_result"].effective_tax_rate * 100
        cg_rate = data["capital_gains_rate"] * 100

        print(f"{loc:<12} {currency_symbol}{take_home_input:>11,.0f}  {currency_symbol}{take_home_input/12:>11,.0f}  {currency_symbol}{col_annual_input:>9,.0f}  {currency_symbol}{col_monthly_input:>9,.0f}  {currency_symbol}{annual_surplus:>11,.0f}  {currency_symbol}{monthly_surplus:>11,.0f}  {tax_rate:>12.2f}%  {cg_rate:>12.0f}%")
