"""
Electric Conversion Calculator for Airbnb Properties
Gas-to-electric cooking conversion benefits analysis
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GasToElectricConverter:
    """Calculate savings from converting gas stoves to electric/induction."""
    
    # Typical costs and usage
    GAS_COST_PER_KG = 8.0  # $/kg for LPG in Caribbean
    GAS_BOTTLE_COST = 50.0  # $ for full 11kg bottle
    GAS_BOTTLE_WEIGHT_KG = 11.0
    
    # Cooking energy usage
    GAS_USAGE_KW_PER_HOUR = 0.5  # Typical gas stove consumption
    INDUCTION_USAGE_KW_PER_HOUR = 1.2  # Induction (more efficient, faster)
    
    # Efficiency
    GAS_THERMAL_EFFICIENCY = 0.40  # 40% of heat reaches food
    INDUCTION_THERMAL_EFFICIENCY = 0.85  # 85% of heat reaches food
    
    # Safety metrics
    GAS_CO中毒_RISK = "Medium"  # Carbon monoxide risk
    GAS_FIRE_RISK = "High"  # Open flame
    GAS_EXPLOSION_RISK = "Low"  # Bottle explosion potential
    
    def __init__(self, property_type: str = "standard"):
        self.property_type = property_type
        self.monthly_gas_usage_kg = self._estimate_monthly_gas()
    
    def _estimate_monthly_gas(self) -> float:
        """Estimate monthly gas usage based on property type."""
        usage_map = {
            "studio": 8.0,
            "1bed": 12.0,
            "2bed": 18.0,
            "3bed": 25.0,
            "large": 35.0,
            "standard": 15.0,
        }
        return usage_map.get(self.property_type, 15.0)
    
    def calculate_savings(self) -> Dict:
        """Calculate monthly and annual savings."""
        # Current gas costs
        monthly_gas_cost = self.monthly_gas_usage_kg * self.GAS_COST_PER_KG
        bottles_per_year = (self.monthly_gas_usage_kg * 12) / self.GAS_BOTTLE_WEIGHT_KG
        
        # Electric cooking costs (induction)
        daily_cooking_hours = 2.0  # Average
        monthly_electric_kwh = self.INDUCTION_USAGE_KW_PER_HOUR * daily_cooking_hours * 30
        electricity_rate = 0.25  # $/kWh
        monthly_electric_cost = monthly_electric_kwh * electricity_rate
        
        # Monthly savings
        monthly_savings = monthly_gas_cost - monthly_electric_cost
        annual_savings = monthly_savings * 12
        
        # One-time costs
        induction_stove_cost = 300.0  # Good induction cooktop
        installation_cost = 150.0  # Electrical work
        total_conversion_cost = induction_stove_cost + installation_cost
        
        # Payback period
        payback_months = total_conversion_cost / monthly_savings if monthly_savings > 0 else 999
        
        return {
            "monthly_gas_cost": round(monthly_gas_cost, 2),
            "monthly_electric_cost": round(monthly_electric_cost, 2),
            "monthly_savings": round(monthly_savings, 2),
            "annual_savings": round(annual_savings, 2),
            "bottles_per_year": round(bottles_per_year, 1),
            "conversion_cost": total_conversion_cost,
            "payback_months": round(payback_months, 1),
            "payback_years": round(payback_months / 12, 1),
        }
    
    def calculate_safety_benefits(self) -> Dict:
        """Calculate safety improvements."""
        return {
            "gas_risk_eliminated": True,
            "fire_risk_reduction": "85%",
            "co_poisoning_risk": "Eliminated",
            "guest_safety_score": {
                "before": 60,  # /100 with gas
                "after": 95,   # /100 with induction
            },
            "insurance_implications": {
                "potential_discount": "5-10%",
                "liability_reduction": "Significant",
            },
            "regulatory_compliance": "Meets modern safety codes",
        }
    
    def generate_proposal(self, host_name: str = "Airbnb Host") -> str:
        """Generate a sales proposal for gas-to-electric conversion."""
        savings = self.calculate_savings()
        safety = self.calculate_safety_benefits()
        
        proposal = f"""
╔══════════════════════════════════════════════════════════════╗
║        🔥 GAS TO ELECTRIC CONVERSION PROPOSAL               ║
║        Power Solution for {host_name:<28} ║
╚══════════════════════════════════════════════════════════════╝

⚡ THE PROBLEM WITH GAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Monthly Gas Costs:          ${savings['monthly_gas_cost']:,.2f}
🧴 Bottles Used Per Year:      {savings['bottles_per_year']:.1f}
💰 Annual Gas Spending:        ${savings['monthly_gas_cost'] * 12:,.2f}

🚨 SAFETY RISKS:
  ✗ Fire hazard from open flame
  ✗ Carbon monoxide poisoning risk
  ✗ Explosion risk from faulty connections
  ✗ Guests stranded with no gas
  ✗ Last-minute gas bottle runs

⚡ THE SOLUTION: INDUCTION COOKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Monthly Electric Cost:       ${savings['monthly_electric_cost']:,.2f}
✅ Monthly Savings:             ${savings['monthly_savings']:,.2f}
✅ Annual Savings:              ${savings['annual_savings']:,.2f}
✅ Payback Period:              {savings['payback_years']:.1f} years

✨ BENEFITS OF INDUCTION:
  • 85% energy efficiency (vs 40% for gas)
  • Faster cooking = happier guests
  • Cooler kitchen (no radiant heat)
  • Easy to clean (smooth surface)
  • Auto-shutoff safety feature

🛡️ SAFETY IMPROVEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEFORE (Gas):
  • Fire Risk: HIGH
  • CO Poisoning: MEDIUM
  • Guest Safety Score: {safety['guest_safety']['before']}/100

AFTER (Induction):
  • Fire Risk: LOW (auto-shutoff)
  • CO Poisoning: ELIMINATED
  • Guest Safety Score: {safety['guest_safety']['after']}/100

💰 INVESTMENT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Induction Cooktop:             ${300}
Installation:                  ${150}
─────────────────────────────────
TOTAL:                         ${savings['conversion_cost']:,.0f}

FINANCING:
  • Include in solar/battery package
  • Monthly payment: ~${savings['conversion_cost'] / 24:,.0f}/month
  • Self-funded from gas savings in {savings['payback_years']:.1f} years

🎯 WHY THIS COMBINES PERFECTLY WITH SOLAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

With your Wind + Battery + BTC Miner system:

1. MORE RENEWABLE ENERGY USAGE
   • Electric cooking uses your generated power
   • No grid dependency for cooking
   • Perfect load matching with solar/wind

2. ENHANCED GUEST EXPERIENCE
   • "Eco-friendly apartment" badge
   • Modern induction cooking (premium feel)
   • No gas smell in the unit
   • Cleaner kitchen environment

3. REDUCED MAINTENANCE
   • No more gas bottle deliveries
   • No more empty bottle anxiety
   • No more guest complaints about running out
   • One less thing to manage

4. MARKET COMPETITIVE ADVANTAGE
   • Safety-conscious travelers prefer electric
   • "Green certified" listing boost
   • Can charge premium rates
   • Attracts long-term renters

📈 FINANCIAL PROJECTION (5 Years)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Year 1:  Save ${savings['annual_savings']:,.0f} - Cost ${savings['conversion_cost']:,.0f} = ${savings['annual_savings'] - savings['conversion_cost']:,.0f}
Year 2:  Save ${savings['annual_savings']:,.0f} = ${savings['annual_savings']:,.0f}
Year 3:  Save ${savings['annual_savings']:,.0f} = ${savings['annual_savings']:,.0f}
Year 4:  Save ${savings['annual_savings']:,.0f} = ${savings['annual_savings']:,.0f}
Year 5:  Save ${savings['annual_savings']:,.0f} = ${savings['annual_savings']:,.0f}

TOTAL 5-YEAR SAVINGS:        ${savings['annual_savings'] * 5 - savings['conversion_cost']:,.0f}

🚀 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Site assessment (free)
2. Induction cooktop recommendation
3. Combined solar + electric package quote
4. Installation scheduling
5. Guest safety certification

💬 PACKAGE OPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Want the COMPLETE energy solution?

🌬️ Wind Turbine + Battery + BTC Miner
+ ⚡ Induction Cooking Conversion
= ZERO energy bills + SAFE cooking + PASSIVE INCOME

Contact us for a bundled quote!

📞 [Your Name]
[Phone] | [Email]
"""
        return proposal


if __name__ == "__main__":
    # Quick test
    converter = GasToElectricConverter(property_type="2bed")
    savings = converter.calculate_savings()
    print(f"Monthly savings: ${savings['monthly_savings']:.2f}")
    print(f"Annual savings: ${savings['annual_savings']:.2f}")
    print(f"Payback: {savings['payback_years']} years")
