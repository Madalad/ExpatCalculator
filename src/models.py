"""Dataclasses shared across the ExpatCalculator package."""
from dataclasses import dataclass
from typing import Optional


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

@dataclass
class InvestmentProjection:
    """Projected wealth growth from investing a share of monthly surplus."""
    years: int
    annual_return: float
    capital_gains_rate: float
    monthly_investment: float
    monthly_cash: float
    total_contributions: float
    portfolio_gross: float
    capital_gains_tax: float
    portfolio_after_tax: float
    cash_total: float
    final_wealth: float
    yearly_wealth: list       # after-tax total wealth if liquidated at end of each year
    yearly_contributed: list  # cumulative surplus put in (invested + cash)
