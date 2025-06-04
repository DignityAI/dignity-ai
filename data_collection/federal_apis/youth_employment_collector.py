# National Youth Employment Data Collection
# For City Bureau investigation: "Defunded and Defiant"
# APIs: USASpending.gov + Department of Labor

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Any

class NationalYouthEmploymentData:
    """
    Collect national federal spending data for youth employment programs
    Focus: Job Corps, AmeriCorps, workforce development cuts 2017-2025
    """
    
    def __init__(self, usaspending_api_key: str = None):
        # Get API key from environment or parameter
        self.usaspending_key = usaspending_api_key or os.getenv('USASPENDING_API_KEY')
        self.usaspending_base = "https://api.usaspending.gov/api/v2/"
        self.dol_base = "https://api.dol.gov/"
        
        # Program identifiers for youth employment
        self.target_programs = {
            'job_corps': {
                'keywords': ['job corps', 'Job Corps'],
                'cfda_numbers': ['17.273'],  # Job Corps CFDA number
                'agency_codes': ['69']  # Department of Labor
            },
            'americorps': {
                'keywords': ['americorps', 'AmeriCorps', 'Corporation for National'],
                'cfda_numbers': ['94.006', '94.013'],  # AmeriCorps programs
                'agency_codes': ['95']  # Corporation for National & Community Service
            },
            'workforce_development': {
                'keywords': ['workforce development', 'youth employment', 'WIOA'],
                'cfda_numbers': ['17.259', '17.278'],  # Workforce development programs
                'agency_codes': ['69']
            }
        }
    
    def get_usaspending_data(self, program_type: str, fiscal_years: List[int]) -> List[Dict]:
        """
        Pull USASpending.gov data for specific youth employment programs
        """
        print(f"Collecting USASpending data for {program_type}...")
        
        program_config = self.target_programs[program_type]
        all_data = []
        
        for year in fiscal_years:
            # Search by CFDA numbers (most reliable)
            for cfda in program_config['cfda_numbers']:
                payload = {
                    "filters": {
                        "time_period": [{
                            "start_date": f"{year}-10-01",
                            "end_date": f"{year+1}-09-30"
                        }],
                        "program_numbers": [cfda]
                    },
                    "fields": [
                        "Award ID",
                        "Recipient Name", 
                        "Award Amount",
                        "Award Type",
                        "Awarding Agency",
                        "Awarding Sub Agency",
                        "Award Description",
                        "Primary Place of Performance City Name",
                        "Primary Place of Performance State Code",
                        "Period of Performance Start Date",
                        "Period of Performance Current End Date"
                    ],
                    "page": 1,
                    "limit": 100
                }
                
                try:
                    response = requests.post(
                        f"{self.usaspending_base}search/spending_by_award/",
                        json=payload,
                        headers={"X-API-Key": self.usaspending_key}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        awards = data.get('results', [])
                        
                        for award in awards:
                            award['fiscal_year'] = year
                            award['program_type'] = program_type
                            award['cfda_number'] = cfda
                            all_data.append(award)
                        
                        print(f"  {year} - CFDA {cfda}: {len(awards)} awards found")
                    else:
                        print(f"  Error for {year} - CFDA {cfda}: {response.status_code}")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    print(f"  Exception for {year} - CFDA {cfda}: {e}")
        
        return all_data
    
    def get_spending_trends(self, program_type: str, fiscal_years: List[int]) -> Dict:
        """
        Get high-level spending trends for program type
        """
        print(f"Getting spending trends for {program_type}...")
        
        program_config = self.target_programs[program_type]
        trends = {}
        
        for year in fiscal_years:
            year_total = 0
            year_count = 0
            
            for cfda in program_config['cfda_numbers']:
                payload = {
                    "group": "fiscal_year",
                    "filters": {
                        "time_period": [{
                            "start_date": f"{year}-10-01", 
                            "end_date": f"{year+1}-09-30"
                        }],
                        "program_numbers": [cfda]
                    }
                }
                
                try:
                    response = requests.post(
                        f"{self.usaspending_base}search/spending_over_time/",
                        json=payload,
                        headers={"X-API-Key": self.usaspending_key}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        for result in results:
                            year_total += float(result.get('aggregated_amount', 0))
                            year_count += int(result.get('award_count', 0))
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  Error getting trends for {year}: {e}")
            
            trends[year] = {
                'total_spending': year_total,
                'award_count': year_count
            }
            
            print(f"  {year}: ${year_total:,.0f} across {year_count} awards")
        
        return trends
    
    def analyze_geographic_distribution(self, program_data: List[Dict]) -> pd.DataFrame:
        """
        Analyze geographic distribution of youth employment funding
        """
        print("Analyzing geographic distribution...")
        
        df = pd.DataFrame(program_data)
        
        if df.empty:
            return pd.DataFrame()
        
        # Group by state and calculate totals
        geo_analysis = df.groupby([
            'Primary Place of Performance State Code',
            'fiscal_year'
        ]).agg({
            'Award Amount': ['sum', 'count', 'mean']
        }).reset_index()
        
        geo_analysis.columns = [
            'state_code', 'fiscal_year', 'total_funding', 'award_count', 'avg_award'
        ]
        
        return geo_analysis
    
    def identify_major_recipients(self, program_data: List[Dict], top_n: int = 20) -> pd.DataFrame:
        """
        Identify major recipients of youth employment funding
        """
        print(f"Identifying top {top_n} recipients...")
        
        df = pd.DataFrame(program_data)
        
        if df.empty:
            return pd.DataFrame()
        
        recipients = df.groupby('Recipient Name').agg({
            'Award Amount': ['sum', 'count'],
            'fiscal_year': ['min', 'max']
        }).reset_index()
        
        recipients.columns = [
            'recipient_name', 'total_funding', 'award_count', 'first_year', 'last_year'
        ]
        
        # Sort by total funding and get top recipients
        top_recipients = recipients.sort_values('total_funding', ascending=False).head(top_n)
        
        return top_recipients
    
    def collect_all_data(self, fiscal_years: List[int] = None) -> Dict[str, Any]:
        """
        Main collection function - gets all data for investigation
        """
        if fiscal_years is None:
            fiscal_years = list(range(2017, 2026))  # 2017-2025
        
        print("="*60)
        print("COLLECTING NATIONAL YOUTH EMPLOYMENT DATA")
        print("="*60)
        
        results = {
            'collection_timestamp': datetime.now().isoformat(),
            'fiscal_years': fiscal_years,
            'programs': {}
        }
        
        for program_type in self.target_programs.keys():
            print(f"\n--- COLLECTING {program_type.upper()} DATA ---")
            
            # Get detailed award data
            award_data = self.get_usaspending_data(program_type, fiscal_years)
            
            # Get spending trends
            trends = self.get_spending_trends(program_type, fiscal_years)
            
            # Analyze geographic distribution
            geo_dist = self.analyze_geographic_distribution(award_data)
            
            # Identify major recipients
            top_recipients = self.identify_major_recipients(award_data)
            
            results['programs'][program_type] = {
                'award_data': award_data,
                'spending_trends': trends,
                'geographic_distribution': geo_dist.to_dict('records') if not geo_dist.empty else [],
                'top_recipients': top_recipients.to_dict('records') if not top_recipients.empty else [],
                'total_awards': len(award_data)
            }
            
            print(f"  Collected {len(award_data)} total awards")
        
        return results
    
    def save_results(self, results: Dict, output_dir: str = "data"):
        """
        Save results to files for analysis
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw JSON
        with open(f"{output_dir}/youth_employment_data_{timestamp}.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save summary CSV for each program
        for program_type, program_data in results['programs'].items():
            # Spending trends
            trends_df = pd.DataFrame.from_dict(
                program_data['spending_trends'], 
                orient='index'
            ).reset_index()
            trends_df.rename(columns={'index': 'fiscal_year'}, inplace=True)
            trends_df.to_csv(f"{output_dir}/{program_type}_spending_trends_{timestamp}.csv", index=False)
            
            # Geographic distribution
            if program_data['geographic_distribution']:
                geo_df = pd.DataFrame(program_data['geographic_distribution'])
                geo_df.to_csv(f"{output_dir}/{program_type}_geographic_{timestamp}.csv", index=False)
            
            # Top recipients
            if program_data['top_recipients']:
                recipients_df = pd.DataFrame(program_data['top_recipients'])
                recipients_df.to_csv(f"{output_dir}/{program_type}_top_recipients_{timestamp}.csv", index=False)
        
        print(f"\nData saved to {output_dir}/ with timestamp {timestamp}")

# Example usage
if __name__ == "__main__":
    # Initialize - API key will be read from environment
    # Set USASPENDING_API_KEY in your Railway environment or .env file
    collector = NationalYouthEmploymentData()
    
    # Collect data for investigation period
    investigation_years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    
    print("Starting data collection for 'Defunded and Defiant' investigation...")
    results = collector.collect_all_data(investigation_years)
    
    # Save results
    collector.save_results(results)
    
    # Print summary
    print("\n" + "="*60)
    print("COLLECTION SUMMARY")
    print("="*60)
    
    for program_type, data in results['programs'].items():
        trends = data['spending_trends']
        print(f"\n{program_type.upper()}:")
        print(f"  Total awards collected: {data['total_awards']}")
        
        if trends:
            years = sorted(trends.keys())
            first_year_spending = trends[years[0]]['total_spending']
            last_year_spending = trends[years[-1]]['total_spending']
            change = last_year_spending - first_year_spending
            pct_change = (change / first_year_spending * 100) if first_year_spending > 0 else 0
            
            print(f"  {years[0]} spending: ${first_year_spending:,.0f}")
            print(f"  {years[-1]} spending: ${last_year_spending:,.0f}")
            print(f"  Change: ${change:,.0f} ({pct_change:+.1f}%)")
    
    print(f"\nData collection complete! Check 'data/' directory for output files.")
