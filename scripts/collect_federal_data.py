#!/usr/bin/env python3
"""
Collect federal youth employment data for Dignity AI training
Integrates with existing Dignity data pipeline
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_collection.federal_apis.youth_employment_collector import NationalYouthEmploymentData

def main():
    """Run federal data collection for Dignity investigation"""
    
    print("="*60)
    print("DIGNITY AI: FEDERAL YOUTH EMPLOYMENT DATA COLLECTION")
    print("="*60)
    
    # Initialize collector
    collector = NationalYouthEmploymentData()
    
    # Focus on recent years for investigation
    investigation_years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    # Collect data
    results = collector.collect_all_data(investigation_years)
    
    # Save to Dignity data structure
    collector.save_results(results, output_dir="data/federal")
    
    print("\nFederal data collection complete!")
    print("Data saved to data/federal/ directory")
    print("Ready for Dignity AI training integration")

if __name__ == "__main__":
    main()
