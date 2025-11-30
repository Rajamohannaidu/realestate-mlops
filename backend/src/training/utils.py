# utils.py

"""
Utility functions for the Real Estate Investment Advisor
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

def setup_logging(log_dir='logs', log_file='app.log'):
    """Setup logging configuration"""
    
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config, config_file='config.json'):
    """Save configuration to JSON file"""
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

def format_currency(amount):
    """Format number as currency"""
    return f"${amount:,.2f}"

def format_percentage(value):
    """Format number as percentage"""
    return f"{value:.2f}%"

def calculate_mortgage_payment(principal, annual_rate, years):
    """
    Calculate monthly mortgage payment
    
    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (e.g., 0.05 for 5%)
        years: Loan term in years
    
    Returns:
        Monthly payment amount
    """
    monthly_rate = annual_rate / 12
    n_payments = years * 12
    
    if monthly_rate == 0:
        return principal / n_payments
    
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / \
                     ((1 + monthly_rate) ** n_payments - 1)
    
    return monthly_payment

def calculate_loan_amortization(principal, annual_rate, years):
    """
    Calculate loan amortization schedule
    
    Returns:
        DataFrame with amortization schedule
    """
    monthly_payment = calculate_mortgage_payment(principal, annual_rate, years)
    monthly_rate = annual_rate / 12
    n_payments = years * 12
    
    schedule = []
    balance = principal
    
    for month in range(1, int(n_payments) + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        
        schedule.append({
            'Month': month,
            'Payment': monthly_payment,
            'Principal': principal_payment,
            'Interest': interest_payment,
            'Balance': max(0, balance)
        })
    
    return pd.DataFrame(schedule)

def validate_property_data(property_data):
    """
    Validate property data inputs
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['area', 'bedrooms', 'bathrooms', 'year_built', 
                      'location', 'property_type']
    
    for field in required_fields:
        if field not in property_data or property_data[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate ranges
    if property_data['area'] <= 0:
        return False, "Area must be positive"
    
    if property_data['bedrooms'] < 0:
        return False, "Bedrooms cannot be negative"
    
    if property_data['year_built'] < 1800 or property_data['year_built'] > datetime.now().year:
        return False, f"Invalid year built: {property_data['year_built']}"
    
    return True, None

def calculate_property_metrics(property_data):
    """
    Calculate derived metrics for a property
    
    Returns:
        Dictionary with calculated metrics
    """
    metrics = {}
    
    # Price per square foot
    if 'price' in property_data and 'area' in property_data:
        metrics['price_per_sqft'] = property_data['price'] / property_data['area']
    
    # Bed-to-bath ratio
    if 'bedrooms' in property_data and 'bathrooms' in property_data:
        metrics['bed_bath_ratio'] = property_data['bedrooms'] / (property_data['bathrooms'] + 1)
    
    # Property age
    if 'year_built' in property_data:
        metrics['property_age'] = datetime.now().year - property_data['year_built']
    
    return metrics

def get_market_statistics(df):
    """
    Calculate market statistics from property dataframe
    
    Returns:
        Dictionary with market statistics
    """
    stats = {
        'total_properties': len(df),
        'avg_price': df['price'].mean() if 'price' in df else None,
        'median_price': df['price'].median() if 'price' in df else None,
        'price_std': df['price'].std() if 'price' in df else None,
        'avg_area': df['area'].mean() if 'area' in df else None,
        'avg_price_per_sqft': (df['price'] / df['area']).mean() if 'price' in df and 'area' in df else None
    }
    
    return stats

def compare_properties(prop1, prop2, metrics=['price', 'roi', 'rental_yield']):
    """
    Compare two properties side by side
    
    Returns:
        Comparison dictionary
    """
    comparison = {}
    
    for metric in metrics:
        if metric in prop1 and metric in prop2:
            value1 = prop1[metric]
            value2 = prop2[metric]
            difference = value1 - value2
            percent_diff = (difference / value2 * 100) if value2 != 0 else 0
            
            comparison[metric] = {
                'property1': value1,
                'property2': value2,
                'difference': difference,
                'percent_difference': percent_diff,
                'better': 1 if value1 > value2 else 2
            }
    
    return comparison

def export_to_csv(data, filename, directory='exports'):
    """Export data to CSV file"""
    
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    
    if isinstance(data, pd.DataFrame):
        data.to_csv(filepath, index=False)
    else:
        pd.DataFrame(data).to_csv(filepath, index=False)
    
    return filepath

def export_to_json(data, filename, directory='exports'):
    """Export data to JSON file"""
    
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4, default=str)
    
    return filepath

def generate_report(property_data, analysis_results, filename='investment_report.txt'):
    """
    Generate text report for investment analysis
    """
    
    report_lines = [
        "=" * 70,
        "REAL ESTATE INVESTMENT ANALYSIS REPORT",
        "=" * 70,
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n" + "=" * 70,
        "PROPERTY DETAILS",
        "=" * 70,
    ]
    
    # Add property details
    for key, value in property_data.items():
        report_lines.append(f"{key.replace('_', ' ').title()}: {value}")
    
    # Add analysis results
    if analysis_results:
        report_lines.extend([
            "\n" + "=" * 70,
            "INVESTMENT ANALYSIS",
            "=" * 70,
        ])
        
        if 'roi' in analysis_results:
            report_lines.append(f"\nROI: {analysis_results['roi']['roi_percentage']:.2f}%")
            report_lines.append(f"Net Profit: {format_currency(analysis_results['roi']['net_profit'])}")
        
        if 'rental_yield' in analysis_results:
            report_lines.append(f"\nGross Rental Yield: {analysis_results['rental_yield']['gross_yield_percentage']:.2f}%")
            report_lines.append(f"Net Rental Yield: {analysis_results['rental_yield']['net_yield_percentage']:.2f}%")
        
        if 'cap_rate' in analysis_results:
            report_lines.append(f"\nCap Rate: {analysis_results['cap_rate']['cap_rate_percentage']:.2f}%")
        
        if 'cash_flow' in analysis_results:
            report_lines.append(f"\nAnnual Cash Flow: {format_currency(analysis_results['cash_flow']['annual_cash_flow'])}")
            report_lines.append(f"Monthly Cash Flow: {format_currency(analysis_results['cash_flow']['monthly_cash_flow'])}")
    
    report_lines.append("\n" + "=" * 70)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 70)
    
    report_text = "\n".join(report_lines)
    
    # Save to file
    os.makedirs('reports', exist_ok=True)
    filepath = os.path.join('reports', filename)
    with open(filepath, 'w') as f:
        f.write(report_text)
    
    return report_text, filepath

def get_risk_assessment(analysis_results):
    """
    Assess investment risk based on metrics
    
    Returns:
        Risk level (Low, Medium, High) and explanation
    """
    risk_score = 0
    risk_factors = []
    
    if 'cash_flow' in analysis_results:
        cash_flow = analysis_results['cash_flow']['annual_cash_flow']
        if cash_flow < 0:
            risk_score += 3
            risk_factors.append("Negative cash flow")
        elif cash_flow < 5000:
            risk_score += 1
            risk_factors.append("Low cash flow")
    
    if 'roi' in analysis_results:
        roi = analysis_results['roi']['roi_percentage']
        if roi < 10:
            risk_score += 2
            risk_factors.append("Low ROI")
    
    if 'rental_yield' in analysis_results:
        yield_val = analysis_results['rental_yield']['net_yield_percentage']
        if yield_val < 3:
            risk_score += 2
            risk_factors.append("Low rental yield")
    
    # Determine risk level
    if risk_score >= 5:
        risk_level = "High"
    elif risk_score >= 3:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'risk_factors': risk_factors
    }

def suggest_improvements(property_data, analysis_results):
    """
    Suggest improvements to enhance investment potential
    """
    suggestions = []
    
    if 'cash_flow' in analysis_results:
        if analysis_results['cash_flow']['annual_cash_flow'] < 10000:
            suggestions.append({
                'category': 'Income',
                'suggestion': 'Consider increasing rental income through property upgrades or better marketing',
                'potential_impact': 'Could improve cash flow by 10-20%'
            })
    
    if 'property_age' in property_data and property_data['property_age'] > 30:
        suggestions.append({
            'category': 'Maintenance',
            'suggestion': 'Older property may need modernization to maintain competitive rental rates',
            'potential_impact': 'Could increase property value by 5-10%'
        })
    
    if 'amenities_score' in property_data and property_data['amenities_score'] < 5:
        suggestions.append({
            'category': 'Amenities',
            'suggestion': 'Add amenities like parking, storage, or upgraded appliances',
            'potential_impact': 'Could justify 5-15% rent increase'
        })
    
    return suggestions

# Example usage
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Utility functions loaded successfully")
    
    # Test mortgage calculation
    monthly_payment = calculate_mortgage_payment(500000, 0.05, 30)
    print(f"Monthly mortgage payment: {format_currency(monthly_payment)}")
    
    # Test property validation
    test_property = {
        'area': 1500,
        'bedrooms': 3,
        'bathrooms': 2,
        'year_built': 2010,
        'location': 'Urban',
        'property_type': 'House'
    }
    
    is_valid, error = validate_property_data(test_property)
    print(f"Property validation: {is_valid}")
    if error:
        print(f"Error: {error}")