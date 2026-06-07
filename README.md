# ExpatCalculator

A Python tool to compare take-home pay and cost of living across different international locations.

## Overview

This project helps expats and remote workers calculate and compare:
- **Income tax** (federal, state, local, and social contributions)
- **Effective tax rates** across different jurisdictions  
- **Take-home pay** after all taxes
- **Cost of living** estimates by lifestyle (low, medium, high)
- **Capital gains tax rates** for investment income
- **Location comparisons** to find the best financial fit

## Supported Locations

- **London, UK** - Complex progressive tax system with National Insurance
- **New York, USA** - Federal, state, and city taxes combined
- **Hong Kong** - Favorable tax environment with no capital gains tax
- **Chicago, USA** - Flat state tax with federal income tax
- **Dubai, UAE** - No income tax jurisdiction
- **Zurich, Switzerland** - Low federal tax with canton-based variations
- **Tokyo, Japan** - Progressive tax system with local inhabitant tax

## Project Structure

```
ExpatCalculator/
├── src/
│   └── script.py           # Main calculator script
├── data/
│   ├── tax_rates.json      # Tax rate data by jurisdiction
│   └── cost_of_living.json # Cost of living estimates
└── README.md               # This file
```

## Data Files

### `tax_rates.json`
Contains income tax brackets, capital gains rates, and social contributions for each location:
- Progressive income tax brackets (where applicable)
- Flat tax rates
- National Insurance / Social Security rates
- Capital gains tax rates
- Special tax considerations

### `cost_of_living.json`
Estimates annual and monthly costs of living by location and lifestyle level:
- **Low**: Modest but comfortable lifestyle (budget housing, local transport)
- **Medium**: Professional standard of living (private flat, entertainment)
- **High**: Luxury lifestyle (premium areas, fine dining, exclusive venues)

Breakdown includes: housing, food, transport, utilities, and other expenses

## Usage

### Basic Usage

```python
from script import TaxCalculator, print_tax_result

# Initialize calculator
calc = TaxCalculator()

# Calculate tax for London with £100,000 income
result = calc.calculate_income_tax(100000, "london")
col = calc.get_cost_of_living("london", "medium")

# Display results
print_tax_result(result, col)
```

### Get Available Locations

```python
locations = calc.get_available_locations()
print(locations)
# Output: ['london', 'new_york', 'hong_kong', 'chicago', 'dubai', 'zurich', 'tokyo']
```

### Compare All Locations

```python
comparison = calc.compare_locations(annual_income=100000, lifestyle="medium")
for location, data in comparison.items():
    print(f"{location}: ${data['tax_result'].take_home_pay:,.0f}")
```

### Get Capital Gains Tax Rate

```python
rate, notes = calc.get_capital_gains_tax_rate("london")
print(f"Capital gains tax: {rate*100}%")
```

### Get Cost of Living Breakdown

```python
col = calc.get_cost_of_living("hong_kong", "high")
print(f"Annual: ${col.annual_total:,.0f}")
print(f"Housing: ${col.housing:,.0f}")
print(f"Food: ${col.food:,.0f}")
```

## Key Results from Example Run

For a $100,000 annual income with medium lifestyle:

| Location | Take-Home | Cost of Living | Surplus |
|----------|-----------|----------------|---------|
| Dubai | $100,000 | $42,000 | $58,000 |
| Hong Kong | $98,000 | $48,000 | $50,000 |
| Zurich | $74,268 | $72,000 | $2,268 |
| Chicago | $73,850 | $50,400 | $23,450 |
| New York | $72,837 | $66,000 | $6,837 |
| Tokyo | $70,300 | $42,000 | $28,300 |
| London | $68,557 | $54,000 | $14,557 |

**Note:** This comparison assumes income is in each location's currency. A real-world comparison should apply exchange rates.

## Tax System Details

### United Kingdom (London)
- Progressive income tax: 0% → 20% → 40% → 45%
- National Insurance: 8% (basic) → 2% (higher earners)
- Capital gains tax: 20% (£3,000 annual allowance)
- Dividend tax: 11.25% (£500 annual allowance)

### United States (New York & Chicago)
- Federal progressive tax: 10% → 37% (7 brackets)
- State tax: NY varies by bracket (up to 10.9%), IL flat 4.95%
- City tax: NYC 3.876%, Chicago 3.8%
- Long-term capital gains: 15% (federal)
- Social Security/Medicare: 7.65%

### Hong Kong
- Progressive tax: 2% → 6% → 10% → 14% → 17%
- **No capital gains tax**
- **No dividends tax** (foreign-sourced income typically exempt)
- Very favorable for investment income

### United Arab Emirates (Dubai)
- **No income tax**
- **No capital gains tax**
- **No corporate tax** (except oil companies)
- One of the world's most tax-friendly jurisdictions

### Switzerland (Zurich)
- Federal progressive tax: 1% → 13.2% (high progressive rate)
- Canton/Local taxes: ~22% typical for Zurich combined
- **No capital gains tax** for long-term holdings
- Employee social contributions: ~8.7%

### Japan (Tokyo)
- Progressive tax: 5% → 45% (7 brackets)
- Local inhabitant tax: ~5%
- Social insurance: ~19.7% (employee + employer)
- Capital gains: 20% for long-term holdings

## Class Reference

### TaxCalculator

**Methods:**
- `calculate_income_tax(annual_income, location)` → TaxResult
- `calculate_tax_on_brackets(income, brackets)` → (total_tax, effective_rate)
- `get_capital_gains_tax_rate(location)` → (rate, notes)
- `get_cost_of_living(location, lifestyle)` → CostOfLivingBreakdown
- `compare_locations(annual_income, lifestyle)` → dict of results
- `get_available_locations()` → list

### TaxResult
```python
@dataclass
class TaxResult:
    gross_income: float
    location: str
    currency: str
    total_tax: float
    income_tax: float
    social_contributions: float
    effective_tax_rate: float
    take_home_pay: float
```

### CostOfLivingBreakdown
```python
@dataclass
class CostOfLivingBreakdown:
    location: str
    lifestyle_level: str
    annual_total: float
    monthly_total: float
    housing: float
    food: float
    transport: float
    utilities: float
    other: float
```

## Future Enhancements

Potential improvements for this project:

1. **Currency Conversion**: Add real-time exchange rate API for accurate comparisons
2. **Additional Locations**: Extend to more cities (Singapore, Toronto, Sydney, etc.)
3. **Web Interface**: Flask/Django web app for easy visualization
4. **Scenario Analysis**: Multiple income streams, business income, investments
5. **Visa/Residency**: Add requirements and costs for different visa categories
6. **Lifestyle Customization**: Allow users to define custom spending profiles
7. **Tax Planning**: Optimization recommendations based on income structure
8. **Historical Tracking**: Monitor tax rate changes over time
9. **Investment Analysis**: Detailed capital gains planning for different scenarios
10. **Retirement Planning**: Long-term projections based on different locations

## Data Sources & Notes

- Tax rates based on 2024-2025 information
- Cost of living estimates converted to USD for comparison
- Rates may change - verify with official tax authorities before making decisions
- This is informational only - consult with tax professionals for actual tax planning
- Currency exchange rates not included - multiply by current rates for real comparisons

## License

This project is provided as-is for informational purposes.

## Disclaimer

This calculator provides estimates only and should not be relied upon for actual tax planning or financial decisions. Tax laws change frequently and vary based on individual circumstances (residency status, employment type, business structure, etc.). 

**Always consult with qualified tax professionals and accountants in your jurisdiction before making any financial or relocation decisions.**
