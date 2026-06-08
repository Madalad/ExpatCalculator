import json
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

# ===== USER INPUT VARIABLES =====

# ANNUAL_INCOME: the annual income amount (currency determined by ANNUAL_INCOME_CURRENCY).
# Example: 100_000 for $100,000 or £100,000 depending on ANNUAL_INCOME_CURRENCY

# ANNUAL_INCOME_CURRENCY: the currency of the ANNUAL_INCOME input.
# Available options: "USD", "GBP"
# The income will be converted to USD, then to the local currency of LOCATION for tax calculations.

# LOCATION: location to calculate taxes and cost of living for.
# Available options: london, new_york, hong_kong, chicago, dubai, zurich, tokyo

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

@dataclass
class TaxBracket:
    """Represents a tax bracket with income range and rate."""
    min_income: float
    max_income: Optional[float]
    rate: float
    description: str = ""

@dataclass
class TaxResult:
    """Result of tax calculation."""
    gross_income: float
    location: str
    currency: str
    exchange_rate_usd: float
    total_tax: float
    income_tax: float
    social_contributions: float
    effective_tax_rate: float
    take_home_pay: float

@dataclass
class CostOfLivingBreakdown:
    """Breakdown of cost of living by category."""
    location: str
    lifestyle_level: str
    annual_total: float
    monthly_total: float
    housing: float
    food: float
    transport: float
    utilities: float
    other: float

class TaxCalculator:
    """Calculate taxes and take-home pay for different locations."""
    
    # Exchange rates to convert from other currencies to USD
    INPUT_CURRENCY_TO_USD = {
        "USD": 1.0,
        "GBP": 1.266,  # Approximate: 1 GBP = 1.266 USD
    }
    
    def __init__(self, tax_data_path: str = None, col_data_path: str = None):
        """Initialize calculator with tax and cost of living data."""
        if tax_data_path is None:
            # Use default path relative to script location
            script_dir = Path(__file__).parent.parent
            tax_data_path = script_dir / "data" / "tax_rates.json"
        if col_data_path is None:
            script_dir = Path(__file__).parent.parent
            col_data_path = script_dir / "data" / "cost_of_living.json"
        
        with open(tax_data_path, 'r') as f:
            self.tax_data = json.load(f)
        
        with open(col_data_path, 'r') as f:
            self.col_data = json.load(f)
    
    def calculate_tax_on_brackets(self, income: float, brackets: list) -> Tuple[float, float]:
        """
        Calculate tax based on progressive tax brackets.
        Returns (total_tax, effective_rate).
        """
        if not brackets:
            return 0, 0
        
        total_tax = 0
        
        for bracket in brackets:
            min_income = bracket["min"]
            max_income = bracket["max"]
            rate = bracket["rate"]
            
            # Skip if income is below this bracket
            if income <= min_income:
                continue
            
            # Calculate taxable amount in this bracket
            if max_income is None:
                # Top bracket
                taxable = income - min_income
            else:
                taxable = min(income, max_income) - min_income
            
            total_tax += taxable * rate
        
        effective_rate = total_tax / income if income > 0 else 0
        return total_tax, effective_rate
    
    def calculate_income_tax(self, annual_income: float, input_currency: str, location: str) -> TaxResult:
        """
        Calculate income tax and take-home pay for a location.
        Converts income from input currency to USD, then to local currency.
        Supports both simple flat rates and progressive brackets.
        """
        if location not in self.tax_data["locations"]:
            raise ValueError(f"Location '{location}' not found in tax data")
        
        if input_currency not in self.INPUT_CURRENCY_TO_USD:
            raise ValueError(f"Currency '{input_currency}' not supported. Choose: {list(self.INPUT_CURRENCY_TO_USD.keys())}")
        
        loc_data = self.tax_data["locations"][location]
        currency = loc_data.get("currency", "USD")
        
        # Convert input currency to USD, then to local currency
        input_to_usd_rate = self.INPUT_CURRENCY_TO_USD[input_currency]
        annual_income_usd = annual_income * input_to_usd_rate
        
        exchange_rate = loc_data.get("exchange_rate_usd", 1.0)  # Default 1.0 for USD locations
        annual_income_local = annual_income_usd * exchange_rate
        
        total_tax = 0
        income_tax = 0
        social_contributions = 0
        
        # Handle zero tax jurisdictions (Dubai)
        if loc_data.get("income_tax_rate") == 0:
            return TaxResult(
                gross_income=annual_income_local,
                location=location,
                currency=currency,
                exchange_rate_usd=exchange_rate,
                total_tax=0,
                income_tax=0,
                social_contributions=0,
                effective_tax_rate=0,
                take_home_pay=annual_income_local
            )
        
        # Federal/National tax (handles both US federal and other national taxes)
        if "federal_income_tax_brackets" in loc_data:
            fed_tax, fed_rate = self.calculate_tax_on_brackets(
                annual_income_local, 
                loc_data["federal_income_tax_brackets"]
            )
            income_tax += fed_tax
        elif "income_tax_brackets" in loc_data:
            # For countries with single progressive tax (UK, Japan, etc.)
            fed_tax, fed_rate = self.calculate_tax_on_brackets(
                annual_income_local,
                loc_data["income_tax_brackets"]
            )
            income_tax += fed_tax
        
        # State/Regional tax
        if "state_income_tax_brackets" in loc_data:
            state_tax, state_rate = self.calculate_tax_on_brackets(
                annual_income_local,
                loc_data["state_income_tax_brackets"]
            )
            income_tax += state_tax
        elif "state_income_tax_rate" in loc_data:
            state_tax = annual_income_local * loc_data["state_income_tax_rate"]
            income_tax += state_tax
        elif "canton_tax_estimate" in loc_data:
            # Switzerland canton tax estimate
            canton_tax = annual_income_local * loc_data["canton_tax_estimate"]
            income_tax += canton_tax
        elif "local_inhabitant_tax" in loc_data:
            # Japan local tax
            local_tax = annual_income_local * loc_data["local_inhabitant_tax"]
            income_tax += local_tax
        
        # Local tax (flat rates)
        if "city_tax" in loc_data:
            city_tax = annual_income_local * loc_data["city_tax"]
            income_tax += city_tax
        
        # National Insurance (UK)
        if "national_insurance_brackets" in loc_data:
            ni_tax, _ = self.calculate_tax_on_brackets(
                annual_income_local,
                loc_data["national_insurance_brackets"]
            )
            social_contributions += ni_tax
        
        # Social insurance/contributions (other countries)
        if "social_insurance_rate" in loc_data:
            social_contributions += annual_income_local * loc_data["social_insurance_rate"]
        
        total_tax = income_tax + social_contributions
        take_home = annual_income_local - total_tax
        effective_rate = (total_tax / annual_income_local) if annual_income_local > 0 else 0
        
        return TaxResult(
            gross_income=annual_income_local,
            location=location,
            currency=currency,
            exchange_rate_usd=exchange_rate,
            total_tax=total_tax,
            income_tax=income_tax,
            social_contributions=social_contributions,
            effective_tax_rate=effective_rate,
            take_home_pay=take_home
        )
    
    def get_capital_gains_tax_rate(self, location: str) -> Tuple[float, str]:
        """Get capital gains tax rate and notes for a location."""
        if location not in self.tax_data["locations"]:
            raise ValueError(f"Location '{location}' not found")
        
        loc_data = self.tax_data["locations"][location]
        rate = loc_data.get("capital_gains_tax_rate", 0)
        notes = loc_data.get("notes", "")
        
        return rate, notes
    
    def get_cost_of_living(self, location: str, lifestyle: str = "medium") -> CostOfLivingBreakdown:
        """Get cost of living breakdown for a location."""
        if location not in self.col_data["locations"]:
            raise ValueError(f"Location '{location}' not found in cost of living data")
        
        loc_data = self.col_data["locations"][location]
        if lifestyle not in loc_data["cost_of_living_brackets"]:
            raise ValueError(f"Lifestyle '{lifestyle}' not found. Choose: low, medium, high")
        
        bracket = loc_data["cost_of_living_brackets"][lifestyle]
        annual_total = bracket["annual_usd"]
        monthly_total = bracket["monthly_usd"]
        
        return CostOfLivingBreakdown(
            location=location,
            lifestyle_level=lifestyle,
            annual_total=annual_total,
            monthly_total=monthly_total,
            housing=annual_total * bracket["housing_percent"],
            food=annual_total * bracket["food_percent"],
            transport=annual_total * bracket["transport_percent"],
            utilities=annual_total * bracket["utilities_percent"],
            other=annual_total * bracket["other_percent"]
        )
    
    def compare_locations(self, annual_income: float, input_currency: str, lifestyle: str = "medium"):
        """Compare all locations for a given income and lifestyle."""
        locations = list(self.tax_data["locations"].keys())
        results = {}
        
        # Get conversion rate from input currency to USD
        input_to_usd = self.INPUT_CURRENCY_TO_USD[input_currency]
        
        for location in locations:
            try:
                tax_result = self.calculate_income_tax(annual_income, input_currency, location)
                col_result = self.get_cost_of_living(location, lifestyle)
                cap_gains_rate, _ = self.get_capital_gains_tax_rate(location)
                
                # Get exchange rate to convert from local currency to USD
                loc_data = self.tax_data["locations"][location]
                exchange_rate = loc_data.get("exchange_rate_usd", 1.0)
                
                # Convert take-home from local currency to USD, then to input currency
                take_home_usd = tax_result.take_home_pay / exchange_rate
                take_home_input = take_home_usd / input_to_usd
                
                # Convert cost of living from USD to input currency
                col_annual_input = col_result.annual_total / input_to_usd
                col_monthly_input = col_result.monthly_total / input_to_usd
                
                # Calculate surplus in input currency
                surplus = take_home_input - col_annual_input
                
                results[location] = {
                    "tax_result": tax_result,
                    "col_result": col_result,
                    "capital_gains_rate": cap_gains_rate,
                    "take_home_input": take_home_input,
                    "col_annual_input": col_annual_input,
                    "col_monthly_input": col_monthly_input,
                    "annual_surplus": surplus,
                    "monthly_surplus": surplus / 12,
                    "input_currency": input_currency
                }
            except Exception as e:
                print(f"Error calculating for {location}: {e}")
        
        return results
    
    def get_available_locations(self) -> list:
        """Get list of available locations."""
        return list(self.tax_data["locations"].keys())


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

def main():
    calculator = TaxCalculator()

    tax_result = calculator.calculate_income_tax(ANNUAL_INCOME, ANNUAL_INCOME_CURRENCY, LOCATION)
    col_result = calculator.get_cost_of_living(LOCATION, LIFESTYLE)
    cap_gains_rate, notes = calculator.get_capital_gains_tax_rate(LOCATION)
    
    print_tax_result(tax_result, col_result, ANNUAL_INCOME_CURRENCY)
    print(f"\nCapital Gains Tax Rate:     {cap_gains_rate*100:.2f}%")
    print(f"Notes: {notes}")
    
    print(f"\n{'COMPARISON ACROSS LOCATIONS':^60}")
    print(f"Income: {ANNUAL_INCOME:,} {ANNUAL_INCOME_CURRENCY} | Lifestyle: {LIFESTYLE}")
    print("="*60)
    
    comparison = calculator.compare_locations(ANNUAL_INCOME, ANNUAL_INCOME_CURRENCY, LIFESTYLE)
    
    # Sort by take-home pay in input currency (descending)
    sorted_comparison = sorted(
        comparison.items(),
        key=lambda x: x[1]["take_home_input"],
        reverse=True
    )
    
    # Get currency symbol
    currency_symbol = "$" if ANNUAL_INCOME_CURRENCY == "USD" else "£"
    
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


if __name__ == "__main__":
    main()