"""Core tax, cost of living, and investment calculations."""
import json
from pathlib import Path
from typing import Tuple

from .currency import fetch_currency_rates
from .models import InvestmentProjection, TaxResult, CostOfLivingBreakdown


class TaxCalculator:
    """Calculate taxes and take-home pay for different locations."""

    # Fetched live at import time; falls back to hardcoded values if unreachable
    INPUT_CURRENCY_TO_USD = fetch_currency_rates()

    def __init__(self, tax_data_path: str = None, col_data_path: str = None, salary_data_path: str = None):
        """Initialize calculator with tax, cost of living, and salary index data."""
        if tax_data_path is None:
            # Use default path relative to script location
            script_dir = Path(__file__).parent.parent
            tax_data_path = script_dir / "data" / "tax_rates.json"
        if col_data_path is None:
            script_dir = Path(__file__).parent.parent
            col_data_path = script_dir / "data" / "cost_of_living.json"
        if salary_data_path is None:
            script_dir = Path(__file__).parent.parent
            salary_data_path = script_dir / "data" / "salary_indices.json"

        with open(tax_data_path, 'r') as f:
            self.tax_data = json.load(f)

        with open(col_data_path, 'r') as f:
            self.col_data = json.load(f)

        with open(salary_data_path, 'r') as f:
            self.salary_data = json.load(f)

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

    def get_salary_index(self, location: str, industry: str = "general") -> float:
        """
        Relative salary level for an industry in a location (New York = 1.00).
        Falls back to the location's 'general' index, then 1.0, when no data exists.
        """
        loc_indices = self.salary_data.get("locations", {}).get(location, {})
        return loc_indices.get(industry, loc_indices.get("general", 1.0))

    def get_available_industries(self) -> list:
        """Get list of industries with salary index data."""
        return self.salary_data.get("industries", ["general"])

    def compare_locations(self, annual_income: float, input_currency: str, lifestyle: str = "medium",
                          normalise_salaries: bool = False, base_location: str = None,
                          industry: str = "general"):
        """
        Compare all locations for a given income and lifestyle.

        With normalise_salaries=True, annual_income is treated as the salary in
        base_location for the given industry, and each location's income is
        scaled by its salary index relative to the base location's.
        """
        locations = list(self.tax_data["locations"].keys())
        results = {}

        # Get conversion rate from input currency to USD
        input_to_usd = self.INPUT_CURRENCY_TO_USD[input_currency]

        base_index = 1.0
        if normalise_salaries:
            if base_location not in self.tax_data["locations"]:
                raise ValueError(f"Base location '{base_location}' not found in tax data")
            base_index = self.get_salary_index(base_location, industry)

        for location in locations:
            try:
                location_income = annual_income
                if normalise_salaries:
                    location_income = annual_income * self.get_salary_index(location, industry) / base_index
                tax_result = self.calculate_income_tax(location_income, input_currency, location)
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
                    "adjusted_income": location_income,
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


def project_investment(monthly_surplus: float, invest_fraction: float,
                       annual_return: float, years: int,
                       capital_gains_rate: float) -> InvestmentProjection:
    """
    Project wealth growth from investing a share of monthly surplus.

    The invested share of a positive surplus earns annual_return compounded
    monthly; the remainder (and any deficit) is held as cash at 0% growth.
    Capital gains tax is applied once, on sale at the end of the horizon.
    All values are in the same currency as monthly_surplus.
    """
    monthly_invest = max(monthly_surplus, 0.0) * invest_fraction
    monthly_cash = monthly_surplus - monthly_invest
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    yearly_wealth = []
    yearly_contributed = []
    gross = contributed = cash = tax = 0.0
    for year in range(1, years + 1):
        n = year * 12
        if monthly_rate > 0:
            gross = monthly_invest * (((1 + monthly_rate) ** n - 1) / monthly_rate)
        else:
            gross = monthly_invest * n
        contributed = monthly_invest * n
        cash = monthly_cash * n
        tax = max(gross - contributed, 0.0) * capital_gains_rate
        yearly_wealth.append(gross - tax + cash)
        yearly_contributed.append(contributed + cash)

    return InvestmentProjection(
        years=years,
        annual_return=annual_return,
        capital_gains_rate=capital_gains_rate,
        monthly_investment=monthly_invest,
        monthly_cash=monthly_cash,
        total_contributions=contributed + cash,
        portfolio_gross=gross,
        capital_gains_tax=tax,
        portfolio_after_tax=gross - tax,
        cash_total=cash,
        final_wealth=gross - tax + cash,
        yearly_wealth=yearly_wealth,
        yearly_contributed=yearly_contributed,
    )
