"""
Energy ROI Calculator for Wind + Battery + BTC Miner Systems
Calculate savings and earnings for Airbnb hosts
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EnergySystem:
    """Model a wind + battery + BTC miner energy system."""
    
    def __init__(
        self,
        wind_capacity_kw: float = 3.0,  # Wind turbine capacity
        battery_capacity_kwh: float = 10.0,  # Battery storage
        battery_cost_per_kwh: float = 150.0,  # $/kWh replacement cost
        btc_miner_watts: float = 1000.0,  # BTC miner power consumption
        electricity_rate: float = 0.25,  # $/kWh (Belize rate)
        connection_fee_monthly: float = 30.0,  # Monthly connection fee
        wind_availability: float = 0.35,  # 35% capacity factor (island wind)
        battery_efficiency: float = 0.90,  # 90% round-trip efficiency
        battery_lifespan_years: int = 10,  # With proper 25-80% cycling
        usdt_export_rate: float = 0.10,  # $/kWh sold back to grid
    ):
        self.wind_capacity_kw = wind_capacity_kw
        self.battery_capacity_kwh = battery_capacity_kwh
        self.battery_cost_per_kwh = battery_cost_per_kwh
        self.btc_miner_watts = btc_miner_watts
        self.electricity_rate = electricity_rate
        self.connection_fee_monthly = connection_fee_monthly
        self.wind_availability = wind_availability
        self.battery_efficiency = battery_efficiency
        self.battery_lifespan_years = battery_lifespan_years
        self.usdt_export_rate = usdt_export_rate
        
        # System costs
        self.wind_system_cost = wind_capacity_kw * 2500  # $2500/kW installed
        self.battery_system_cost = battery_capacity_kwh * 800  # $800/kWh
        self.btc_miner_cost = btc_miner_watts / 1000 * 500  # $500 per kW
        
        # Optimal battery range (25-80% = 55% usable)
        self.min_soc = 0.25
        self.max_soc = 0.80
        self.usable_battery_capacity = battery_capacity_kwh * (self.max_soc - self.min_soc)
    
    def calculate_monthly_savings(self) -> Dict:
        """Calculate monthly energy savings."""
        # Wind generation
        monthly_wind_kwh = self.wind_capacity_kw * 24 * 30 * self.wind_availability
        
        # Battery cycling (daily)
        daily_cycles = 1  # One full cycle per day in optimal range
        monthly_battery_loss = monthly_wind_kwh * (1 - self.battery_efficiency)
        
        # BTC miner as smart load
        # Runs when battery > 80% or < 25%
        miner_running_hours = 8  # Average hours per day
        monthly_miner_kwh = (self.btc_miner_watts / 1000) * miner_running_hours * 30
        
        # Grid consumption (after system)
        old_monthly_kwh = 500  # Average Airbnb property usage
        new_monthly_kwh = max(0, old_monthly_kwh - monthly_wind_kwh + monthly_miner_kwh)
        
        # Savings
        old_cost = old_monthly_kwh * self.electricity_rate + self.connection_fee_monthly
        new_cost = new_monthly_kwh * self.electricity_rate + self.connection_fee_monthly
        monthly_savings = old_cost - new_cost
        
        # USDT earnings from excess export
        excess_kwh = max(0, monthly_wind_kwh - monthly_miner_kwh - (old_monthly_kwh * 0.1))
        monthly_usdt_earnings = excess_kwh * self.usdt_export_rate
        
        return {
            "monthly_wind_generated_kwh": round(monthly_wind_kwh, 1),
            "monthly_miner_consumption_kwh": round(monthly_miner_kwh, 1),
            "monthly_grid_consumption_kwh": round(new_monthly_kwh, 1),
            "monthly_savings_usd": round(monthly_savings, 2),
            "monthly_usdt_earnings": round(monthly_usdt_earnings, 2),
            "total_monthly_benefit": round(monthly_savings + monthly_usdt_earnings, 2),
            "excess_energy_for_export_kwh": round(excess_kwh, 1),
        }
    
    def calculate_roi(self) -> Dict:
        """Calculate return on investment."""
        total_system_cost = (
            self.wind_system_cost +
            self.battery_system_cost +
            self.btc_miner_cost
        )
        
        monthly_data = self.calculate_monthly_savings()
        monthly_benefit = monthly_data["total_monthly_benefit"]
        annual_benefit = monthly_benefit * 12
        
        # Battery replacement (every 10 years with 25-80% cycling)
        annual_battery_cost = (
            self.battery_capacity_kwh * self.battery_cost_per_kwh / self.battery_lifespan_years
        )
        
        net_annual_benefit = annual_benefit - annual_battery_cost
        payback_months = total_system_cost / monthly_benefit if monthly_benefit > 0 else 999
        
        return {
            "total_system_cost_usd": round(total_system_cost, 0),
            "wind_system_cost": round(self.wind_system_cost, 0),
            "battery_system_cost": round(self.battery_system_cost, 0),
            "btc_miner_cost": round(self.btc_miner_cost, 0),
            "annual_benefit_usd": round(annual_benefit, 0),
            "annual_battery_replacement": round(annual_battery_cost, 0),
            "net_annual_benefit_usd": round(net_annual_benefit, 0),
            "payback_months": round(payback_months, 1),
            "payback_years": round(payback_months / 12, 1),
            "roi_5year_percent": round(
                (net_annual_benefit * 5 - total_system_cost) / total_system_cost * 100, 1
            ),
            "battery_lifespan_years": self.battery_lifespan_years,
            "optimal_range": "25-80% SOC",
        }
    
    def generate_proposal(self, host_name: str = "Airbnb Host") -> str:
        """Generate a sales proposal for the host."""
        savings = self.calculate_monthly_savings()
        roi = self.calculate_roi()
        
        proposal = f"""
╔══════════════════════════════════════════════════════════════╗
║           🌬️ WIND + BATTERY + BTC MINER SYSTEM              ║
║              Power Solution for {host_name:<28} ║
╚══════════════════════════════════════════════════════════════╝

📊 MONTHLY BENEFITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Electricity Savings:     ${savings['monthly_savings_usd']:,.2f}/month
💵 USDT Energy Export:      ${savings['monthly_usdt_earnings']:,.2f}/month
📈 Total Monthly Benefit:   ${savings['total_monthly_benefit']:,.2f}/month
📆 Annual Benefit:          ${savings['total_monthly_benefit'] * 12:,.2f}

⚡ ENERGY FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌬️  Wind Generated:      {savings['monthly_wind_generated_kwh']:,.0f} kWh/month
🔋 Battery Storage:       {self.battery_capacity_kwh} kWh (55% usable: 25-80%)
⛏️  BTC Miner Load:       {savings['monthly_miner_consumption_kwh']:,.0f} kWh/month
   (Smart load - regulates battery)
🏠 Grid Consumption:      {savings['monthly_grid_consumption_kwh']:,.0f} kWh/month
   (Connection fee only: ${self.connection_fee_monthly}/month)

🔋 BATTERY LIFE EXTENSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Optimal range: 25-80% State of Charge
✓ Avoids overcharging (100%) - prevents degradation
✓ Avoids deep discharge (<25%) - prevents sulfation
✓ Expected lifespan: {self.battery_lifespan_years} years (vs 5 years without regulation)
✓ BTC Miner acts as "pressure relief valve"

💰 INVESTMENT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

System Costs:
  Wind Turbine ({self.wind_capacity_kw}kW):    ${roi['wind_system_cost']:,.0f}
  Battery ({self.battery_capacity_kwh}kWh):      ${roi['battery_system_cost']:,.0f}
  BTC Miner ({int(self.btc_miner_watts)}W):       ${roi['btc_miner_cost']:,.0f}
  ─────────────────────────────────
  TOTAL:                    ${roi['total_system_cost_usd']:,.0f}

Financing Options:
  • 36 months @ 8% = ${roi['total_system_cost_usd'] / 36 * 1.08:,.0f}/month
  • 60 months @ 10% = ${roi['total_system_cost_usd'] / 60 * 1.10:,.0f}/month
  • Lease option available

📈 ROI ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Payback Period:         {roi['payback_years']:.1f} years ({roi['payback_months']:.0f} months)
5-Year ROI:             {roi['roi_5year_percent']:.1f}%
Annual Net Benefit:     ${roi['net_annual_benefit_usd']:,.0f}

✅ WHY THIS WORKS FOR AIRBNB HOSTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. REDUCED OPERATING COSTS
   • Cut electricity bill by ${savings['monthly_savings_usd']:,.0f}/month
   • Pay only connection fee (${self.connection_fee_monthly}/month)
   • Predictable energy costs = better profit margins

2. BETTER GUEST EXPERIENCE
   • No more power outage complaints
   • Reliable AC, hot water, lights 24/7
   • "Eco-friendly property" marketing advantage
   • Can charge premium rates for green accommodation

3. PASSIVE INCOME STREAM
   • Sell excess energy as USDT
   • ${savings['monthly_usdt_earnings']:,.2f}/month average
   • Blockchain-recorded transactions
   • Can reinvest in more systems

4. LONG-TERM VALUE
   • Battery lasts {self.battery_lifespan_years}x longer with regulation
   • Increases property value
   • Future-proof against energy price hikes
   • Tax deductions available

🎯 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Site survey (free) - Assess wind potential at your location
2. System design - Custom sizing for your property
3. Installation - Professional setup (1-2 days)
4. Monitoring - Track savings via mobile app
5. Expansion - Add more units as you scale

📞 CONTACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to power your Airbnb sustainably?

[Your Name]
[Your Company]
[Phone] | [Email] | [Website]

"Let your wind pay for itself while your guests sleep soundly.""
"""
        return proposal


class LocationEnergyCalculator:
    """Calculate energy potential for a specific location."""
    
    def __init__(self, location_name: str):
        self.location_name = location_name
        self.location_data = self._load_location_data()
    
    def _load_location_data(self) -> dict:
        """Load location-specific energy data."""
        # Default Belize/Caribbean data
        return {
            "avg_wind_speed_mps": 6.5,  # m/s (good for islands)
            "capacity_factor": 0.35,  # 35% (island wind)
            "electricity_rate": 0.25,  # $/kWh
            "sunshine_hours": 5.5,  # hours/day
            "typical_property_kwh": 500,  # monthly usage
            "connection_fee": 30.0,  # monthly
        }
    
    def calculate_for_location(self, property_count: int = 1) -> Dict:
        """Calculate energy potential for a location."""
        system = EnergySystem(
            wind_capacity_kw=3.0,
            battery_capacity_kwh=10.0,
            wind_availability=self.location_data["capacity_factor"],
            electricity_rate=self.location_data["electricity_rate"],
            connection_fee_monthly=self.location_data["connection_fee"],
        )
        
        savings = system.calculate_monthly_savings()
        roi = system.calculate_roi()
        
        # Scale for multiple properties
        return {
            "location": self.location_name,
            "property_count": property_count,
            "system": {
                "wind_capacity_kw": system.wind_capacity_kw,
                "battery_capacity_kwh": system.battery_capacity_kwh,
                "btc_miner_watts": system.btc_miner_watts,
            },
            "monthly_per_property": savings,
            "monthly_total": {
                "savings": round(savings["monthly_savings_usd"] * property_count, 2),
                "usdt_earnings": round(savings["monthly_usdt_earnings"] * property_count, 2),
                "total": round(savings["total_monthly_benefit"] * property_count, 2),
            },
            "roi": roi,
            "prophecies": [
                f"Each property saves ~${savings['monthly_savings_usd']:,.0f}/month",
                f"Payback in {roi['payback_years']:.1f} years",
                f"BTC miner extends battery life by 2x",
            ],
        }


if __name__ == "__main__":
    # Quick test
    calc = LocationEnergyCalculator("Ambergris Caye")
    result = calc.calculate_for_location(property_count=5)
    print(result["monthly_total"])
