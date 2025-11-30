# src/investment_analytics.py

import numpy as np
import pandas as pd

class InvestmentAnalytics:
    """Calculate investment metrics for real estate properties"""
    
    def __init__(self):
        self.default_appreciation_rate = 0.04  # 4% annual
        self.default_vacancy_rate = 0.05  # 5%
        self.default_maintenance_rate = 0.01  # 1% of property value
        
    def calculate_roi(self, purchase_price, annual_rental_income, 
                     operating_expenses, holding_period_years=5):
        """
        Calculate Return on Investment (ROI)
        ROI = (Net Profit / Total Investment) * 100
        """
        total_rental_income = annual_rental_income * holding_period_years
        total_expenses = operating_expenses * holding_period_years
        
        # Estimate future property value with appreciation
        future_value = purchase_price * (1 + self.default_appreciation_rate) ** holding_period_years
        
        # Calculate net profit
        net_profit = (future_value - purchase_price) + (total_rental_income - total_expenses)
        
        roi = (net_profit / purchase_price) * 100
        
        return {
            'roi_percentage': roi,
            'net_profit': net_profit,
            'future_property_value': future_value,
            'total_rental_income': total_rental_income,
            'total_expenses': total_expenses
        }
    
    def calculate_rental_yield(self, purchase_price, annual_rental_income):
        """
        Calculate Rental Yield
        Rental Yield = (Annual Rental Income / Property Price) * 100
        """
        gross_yield = (annual_rental_income / purchase_price) * 100
        
        # Net yield (accounting for expenses)
        annual_expenses = purchase_price * (self.default_maintenance_rate + self.default_vacancy_rate)
        net_rental_income = annual_rental_income - annual_expenses
        net_yield = (net_rental_income / purchase_price) * 100
        
        return {
            'gross_yield_percentage': gross_yield,
            'net_yield_percentage': net_yield,
            'annual_rental_income': annual_rental_income,
            'annual_expenses': annual_expenses,
            'net_annual_income': net_rental_income
        }
    
    def calculate_appreciation(self, purchase_price, years=5, 
                              appreciation_rate=None):
        """
        Calculate property price appreciation over time
        """
        if appreciation_rate is None:
            appreciation_rate = self.default_appreciation_rate
        
        appreciation_schedule = []
        current_value = purchase_price
        
        for year in range(1, years + 1):
            current_value = current_value * (1 + appreciation_rate)
            appreciation_amount = current_value - purchase_price
            appreciation_percentage = (appreciation_amount / purchase_price) * 100
            
            appreciation_schedule.append({
                'year': year,
                'property_value': current_value,
                'appreciation_amount': appreciation_amount,
                'appreciation_percentage': appreciation_percentage
            })
        
        return {
            'appreciation_schedule': appreciation_schedule,
            'final_value': current_value,
            'total_appreciation': current_value - purchase_price,
            'total_appreciation_percentage': ((current_value - purchase_price) / purchase_price) * 100
        }
    
    def calculate_cash_flow(self, purchase_price, annual_rental_income,
                           mortgage_payment=0, property_tax=0,
                           insurance=0, maintenance=0):
        """
        Calculate annual cash flow
        Cash Flow = Income - Expenses
        """
        # If maintenance not provided, estimate as 1% of property value
        if maintenance == 0:
            maintenance = purchase_price * self.default_maintenance_rate
        
        total_expenses = mortgage_payment + property_tax + insurance + maintenance
        
        # Account for vacancy
        effective_rental_income = annual_rental_income * (1 - self.default_vacancy_rate)
        
        annual_cash_flow = effective_rental_income - total_expenses
        monthly_cash_flow = annual_cash_flow / 12
        
        return {
            'annual_cash_flow': annual_cash_flow,
            'monthly_cash_flow': monthly_cash_flow,
            'effective_rental_income': effective_rental_income,
            'total_annual_expenses': total_expenses,
            'cash_on_cash_return': (annual_cash_flow / purchase_price) * 100
        }
    
    def calculate_cap_rate(self, purchase_price, annual_rental_income,
                          operating_expenses=None):
        """
        Calculate Capitalization Rate
        Cap Rate = (Net Operating Income / Property Price) * 100
        """
        if operating_expenses is None:
            operating_expenses = purchase_price * (self.default_maintenance_rate + self.default_vacancy_rate)
        
        net_operating_income = annual_rental_income - operating_expenses
        cap_rate = (net_operating_income / purchase_price) * 100
        
        return {
            'cap_rate_percentage': cap_rate,
            'net_operating_income': net_operating_income,
            'annual_rental_income': annual_rental_income,
            'operating_expenses': operating_expenses
        }
    
    def calculate_break_even_point(self, purchase_price, annual_rental_income,
                                   annual_expenses):
        """
        Calculate break-even period
        """
        annual_net_income = annual_rental_income - annual_expenses
        
        if annual_net_income <= 0:
            return {
                'break_even_years': None,
                'message': 'Property generates negative cash flow'
            }
        
        break_even_years = purchase_price / annual_net_income
        
        return {
            'break_even_years': break_even_years,
            'annual_net_income': annual_net_income,
            'message': f'Break-even in {break_even_years:.1f} years'
        }
    
    def comprehensive_analysis(self, property_data):
        """
        Perform comprehensive investment analysis
        
        property_data should contain:
        - purchase_price
        - annual_rental_income
        - operating_expenses (optional)
        - holding_period_years (optional)
        """
        purchase_price = property_data['purchase_price']
        annual_rental_income = property_data.get('annual_rental_income', purchase_price * 0.05)
        operating_expenses = property_data.get('operating_expenses', purchase_price * 0.02)
        holding_period = property_data.get('holding_period_years', 5)
        
        analysis = {
            'property_price': purchase_price,
            'roi': self.calculate_roi(purchase_price, annual_rental_income, 
                                     operating_expenses, holding_period),
            'rental_yield': self.calculate_rental_yield(purchase_price, annual_rental_income),
            'appreciation': self.calculate_appreciation(purchase_price, holding_period),
            'cash_flow': self.calculate_cash_flow(purchase_price, annual_rental_income),
            'cap_rate': self.calculate_cap_rate(purchase_price, annual_rental_income),
            'break_even': self.calculate_break_even_point(purchase_price, annual_rental_income, 
                                                          operating_expenses)
        }
        
        return analysis
    
    def investment_recommendation(self, analysis):
        """
        Provide investment recommendation based on metrics
        """
        roi = analysis['roi']['roi_percentage']
        rental_yield = analysis['rental_yield']['net_yield_percentage']
        cap_rate = analysis['cap_rate']['cap_rate_percentage']
        cash_flow = analysis['cash_flow']['annual_cash_flow']
        
        score = 0
        recommendations = []
        
        # ROI evaluation
        if roi > 50:
            score += 3
            recommendations.append("Excellent ROI potential")
        elif roi > 30:
            score += 2
            recommendations.append("Good ROI potential")
        elif roi > 15:
            score += 1
            recommendations.append("Moderate ROI potential")
        else:
            recommendations.append("Low ROI - consider other options")
        
        # Rental yield evaluation
        if rental_yield > 6:
            score += 3
            recommendations.append("Strong rental yield")
        elif rental_yield > 4:
            score += 2
            recommendations.append("Acceptable rental yield")
        else:
            recommendations.append("Low rental yield")
        
        # Cap rate evaluation
        if cap_rate > 8:
            score += 2
            recommendations.append("Attractive cap rate")
        elif cap_rate > 5:
            score += 1
            recommendations.append("Fair cap rate")
        
        # Cash flow evaluation
        if cash_flow > 0:
            score += 2
            recommendations.append("Positive cash flow")
        else:
            recommendations.append("Negative cash flow - requires capital")
        
        # Overall recommendation
        if score >= 8:
            overall = "STRONG BUY - Excellent investment opportunity"
        elif score >= 5:
            overall = "BUY - Good investment potential"
        elif score >= 3:
            overall = "HOLD - Consider carefully"
        else:
            overall = "AVOID - Poor investment metrics"
        
        return {
            'score': score,
            'overall_recommendation': overall,
            'detailed_recommendations': recommendations
        }

# Example usage
if __name__ == "__main__":
    analytics = InvestmentAnalytics()
    
    # Example property
    property_data = {
        'purchase_price': 500000,
        'annual_rental_income': 30000,
        'operating_expenses': 8000,
        'holding_period_years': 5
    }
    
    # Perform comprehensive analysis
    analysis = analytics.comprehensive_analysis(property_data)
    
    print("=== INVESTMENT ANALYSIS ===\n")
    print(f"Property Price: ${analysis['property_price']:,.2f}\n")
    
    print(f"ROI: {analysis['roi']['roi_percentage']:.2f}%")
    print(f"Net Profit (5 years): ${analysis['roi']['net_profit']:,.2f}\n")
    
    print(f"Gross Rental Yield: {analysis['rental_yield']['gross_yield_percentage']:.2f}%")
    print(f"Net Rental Yield: {analysis['rental_yield']['net_yield_percentage']:.2f}%\n")
    
    print(f"Cap Rate: {analysis['cap_rate']['cap_rate_percentage']:.2f}%\n")
    
    print(f"Annual Cash Flow: ${analysis['cash_flow']['annual_cash_flow']:,.2f}")
    print(f"Monthly Cash Flow: ${analysis['cash_flow']['monthly_cash_flow']:,.2f}\n")
    
    # Get recommendation
    recommendation = analytics.investment_recommendation(analysis)
    print(f"Investment Score: {recommendation['score']}/10")
    print(f"Recommendation: {recommendation['overall_recommendation']}")
    print("\nDetails:")
    for rec in recommendation['detailed_recommendations']:
        print(f"  • {rec}")