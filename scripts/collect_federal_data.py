#!/usr/bin/env python3
"""
Detailed Federal Youth Employment Data Collector
Gets the specific organizational and geographic data needed for investigation
"""

import requests
import pandas as pd
import json
import time
import os
from datetime import datetime

class DetailedFederalCollector:
    """
    Collect detailed data on specific organizations, contracts, and cuts
    """
    
    def __init__(self):
        self.api_key = os.getenv('USASPENDING_API_KEY')
        self.base_url = "https://api.usaspending.gov/api/v2/"
        
        # Specific programs we care about
        self.programs = {
            'job_corps': {
                'keywords': ['Job Corps', 'job corps'],
                'def_codes': ['O', 'A', 'B'],  # Contracts, grants, loans
                'agencies': ['Department of Labor', 'DOL']
            },
            'americorps': {
                'keywords': ['AmeriCorps', 'americorps', 'Corporation for National'],
                'def_codes': ['A', 'B'],  # Grants primarily
                'agencies': ['Corporation for National and Community Service']
            }
        }
    
    def search_detailed_awards(self, keywords, fiscal_year, limit=500):
        """
        Search for detailed award information
        """
        print(f"  Searching for '{', '.join(keywords)}' in {fiscal_year}...")
        
        payload = {
            "filters": {
                "keywords": keywords,
                "time_period": [{
                    "start_date": f"{fiscal_year}-10-01",
                    "end_date": f"{fiscal_year+1}-09-30"
                }]
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Recipient DUNS",
                "Award Amount",
                "Award Type",
                "Award Description", 
                "Awarding Agency",
                "Awarding Sub Agency",
                "Primary Place of Performance City Name",
                "Primary Place of Performance State Code",
                "Primary Place of Performance Country Code",
                "Period of Performance Start Date",
                "Period of Performance Current End Date",
                "Last Modified Date"
            ],
            "page": 1,
            "limit": limit,
            "sort": "Award Amount",
            "order": "desc"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}search/spending_by_award/",
                json=payload,
                headers={"X-API-Key": self.api_key} if self.api_key else {}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"    Found {len(results)} awards")
                return results
            else:
                print(f"    Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"    Exception: {e}")
            return []
    
    def get_recipient_details(self, recipient_name):
        """
        Get more details about a specific recipient
        """
        payload = {
            "filters": {
                "recipient_search_text": [recipient_name]
            },
            "fields": [
                "recipient_name",
                "total_transaction_amount",
                "award_count"
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}search/spending_by_recipient/",
                json=payload,
                headers={"X-API-Key": self.api_key} if self.api_key else {}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []
            
        except Exception as e:
            print(f"Error getting recipient details: {e}")
            return []
    
    def analyze_cuts_by_organization(self, program_data):
        """
        Find organizations that lost funding between years
        """
        print("  Analyzing funding cuts by organization...")
        
        # Group by recipient and year
        df = pd.DataFrame(program_data)
        if df.empty:
            return []
        
        # Convert dates and amounts
        df['Award Amount'] = pd.to_numeric(df['Award Amount'], errors='coerce')
        df['fiscal_year'] = df['fiscal_year']
        
        # Group by recipient and year
        recipient_yearly = df.groupby(['Recipient Name', 'fiscal_year']).agg({
            'Award Amount': 'sum',
            'Award ID': 'count'
        }).reset_index()
        
        recipient_yearly.columns = ['recipient', 'year', 'total_amount', 'award_count']
        
        # Find recipients who had funding in early years but not recent years
        cuts_analysis = []
        
        for recipient in recipient_yearly['recipient'].unique():
            recipient_data = recipient_yearly[recipient_yearly['recipient'] == recipient]
            
            years = sorted(recipient_data['year'].tolist())
            if len(years) < 2:
                continue
            
            # Compare first half vs second half of years
            mid_point = len(years) // 2
            early_years = years[:mid_point] if mid_point > 0 else [years[0]]
            recent_years = years[mid_point:] if mid_point > 0 else [years[-1]]
            
            early_funding = recipient_data[recipient_data['year'].isin(early_years)]['total_amount'].sum()
            recent_funding = recipient_data[recipient_data['year'].isin(recent_years)]['total_amount'].sum()
            
            funding_change = recent_funding - early_funding
            pct_change = (funding_change / early_funding * 100) if early_funding > 0 else 0
            
            cuts_analysis.append({
                'recipient': recipient,
                'early_years': early_years,
                'recent_years': recent_years,
                'early_funding': early_funding,
                'recent_funding': recent_funding,
                'funding_change': funding_change,
                'pct_change': pct_change,
                'cut_amount': abs(funding_change) if funding_change < 0 else 0
            })
        
        # Sort by biggest cuts
        cuts_analysis.sort(key=lambda x: x['cut_amount'], reverse=True)
        
        return cuts_analysis
    
    def find_chicago_impacts(self, program_data):
        """
        Find specific Chicago/Illinois impacts
        """
        print("  Analyzing Chicago/Illinois impacts...")
        
        df = pd.DataFrame(program_data)
        if df.empty:
            return []
        
        # Filter for Illinois
        illinois_data = df[df['Primary Place of Performance State Code'] == 'IL'].copy()
        
        if illinois_data.empty:
            return []
        
        illinois_data['Award Amount'] = pd.to_numeric(illinois_data['Award Amount'], errors='coerce')
        
        # Group by recipient in Illinois
        illinois_recipients = illinois_data.groupby(['Recipient Name', 'fiscal_year']).agg({
            'Award Amount': 'sum',
            'Award ID': 'count'
        }).reset_index()
        
        return illinois_recipients.to_dict('records')
    
    def collect_investigation_data(self, years=[2020, 2021, 2022, 2023, 2024, 2025]):
        """
        Collect the detailed data needed for investigation
        """
        print("="*60)
        print("COLLECTING DETAILED INVESTIGATION DATA")
        print("="*60)
        
        all_data = {
            'collection_time': datetime.now().isoformat(),
            'programs': {}
        }
        
        for program_type, config in self.programs.items():
            print(f"\n--- {program_type.upper()} DETAILED COLLECTION ---")
            
            program_awards = []
            
            # Get detailed awards for each year
            for year in years:
                awards = self.search_detailed_awards(config['keywords'], year)
                
                for award in awards:
                    award['fiscal_year'] = year
                    award['program_type'] = program_type
                    program_awards.append(award)
                
                time.sleep(1)  # Rate limiting
            
            # Analyze cuts by organization
            cuts_analysis = self.analyze_cuts_by_organization(program_awards)
            
            # Find Chicago impacts
            chicago_impacts = self.find_chicago_impacts(program_awards)
            
            all_data['programs'][program_type] = {
                'total_awards': len(program_awards),
                'raw_awards': program_awards,
                'cuts_by_organization': cuts_analysis[:20],  # Top 20 biggest cuts
                'chicago_illinois_impacts': chicago_impacts
            }
            
            print(f"  Collected {len(program_awards)} detailed awards")
            print(f"  Identified {len(cuts_analysis)} organizations with funding changes")
            print(f"  Found {len(chicago_impacts)} Illinois impacts")
        
        return all_data
    
    def save_investigation_data(self, data, output_dir="data"):
        """
        Save detailed data in investigation-ready format
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full JSON
        with open(f"{output_dir}/detailed_investigation_data_{timestamp}.json", 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Create investigation-ready CSV files
        for program_type, program_data in data['programs'].items():
            
            # Organizations that lost funding
            if program_data['cuts_by_organization']:
                cuts_df = pd.DataFrame(program_data['cuts_by_organization'])
                cuts_df.to_csv(f"{output_dir}/{program_type}_funding_cuts_{timestamp}.csv", index=False)
                print(f"Saved: {program_type}_funding_cuts_{timestamp}.csv")
            
            # All awards by year
            if program_data['raw_awards']:
                awards_df = pd.DataFrame(program_data['raw_awards'])
                awards_df.to_csv(f"{output_dir}/{program_type}_all_awards_{timestamp}.csv", index=False)
                print(f"Saved: {program_type}_all_awards_{timestamp}.csv")
            
            # Chicago/Illinois specific impacts
            if program_data['chicago_illinois_impacts']:
                chicago_df = pd.DataFrame(program_data['chicago_illinois_impacts'])
                chicago_df.to_csv(f"{output_dir}/{program_type}_illinois_impacts_{timestamp}.csv", index=False)
                print(f"Saved: {program_type}_illinois_impacts_{timestamp}.csv")
        
        print(f"\nInvestigation data saved with timestamp: {timestamp}")
        return timestamp
    
    def generate_investigation_summary(self, data):
        """
        Generate investigation-ready summary
        """
        print("\n" + "="*60)
        print("INVESTIGATION SUMMARY")
        print("="*60)
        
        for program_type, program_data in data['programs'].items():
            print(f"\n{program_type.upper()} FINDINGS:")
            print("-" * 40)
            
            # Biggest organizational cuts
            cuts = program_data['cuts_by_organization']
            if cuts:
                print(f"🔻 TOP ORGANIZATIONS THAT LOST FUNDING:")
                for i, org in enumerate(cuts[:10]):
                    if org['cut_amount'] > 0:
                        name = org['recipient'][:50] + "..." if len(org['recipient']) > 50 else org['recipient']
                        print(f"   {i+1:2d}. {name}")
                        print(f"       Lost: ${org['cut_amount']:,.0f} ({org['pct_change']:.1f}% decrease)")
            
            # Chicago impacts
            chicago_impacts = program_data['chicago_illinois_impacts']
            if chicago_impacts:
                print(f"\n🏢 ILLINOIS ORGANIZATIONS AFFECTED:")
                chicago_df = pd.DataFrame(chicago_impacts)
                if not chicago_df.empty:
                    for recipient in chicago_df['Recipient Name'].unique()[:10]:
                        recipient_data = chicago_df[chicago_df['Recipient Name'] == recipient]
                        total_funding = recipient_data['Award Amount'].sum()
                        years = recipient_data['fiscal_year'].tolist()
                        name = recipient[:50] + "..." if len(recipient) > 50 else recipient
                        print(f"   • {name}: ${total_funding:,.0f} ({min(years)}-{max(years)})")
        
        print(f"\n📰 INVESTIGATION ANGLES:")
        print("   • Specific organizations that lost federal funding")
        print("   • Chicago/Illinois community impacts")
        print("   • Dollar amounts of cuts by recipient")
        print("   • Timeline of when cuts happened")

if __name__ == "__main__":
    collector = DetailedFederalCollector()
    
    print("Collecting detailed federal data for investigation...")
    data = collector.collect_investigation_data()
    
    timestamp = collector.save_investigation_data(data)
    collector.generate_investigation_summary(data)
    
    print(f"\n✅ DETAILED DATA COLLECTION COMPLETE")
    print(f"Check 'data/' folder for investigation-ready CSV files")
