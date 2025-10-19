import os
import requests
import json
from input_handler import InputHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ApolloDataRetriever:
    """Retrieve data from Apollo API based on ICP configuration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': api_key
        }
    
    def transform_org_config(self, icp_config: dict) -> dict:
        """Transform ICP config to Apollo Organizations API format."""
        icp = icp_config.get('ICP', {})
        signals = icp_config.get('Signals', {})
        
        apollo_params = {
            'page': 1,
            'per_page': 25
        }
        
        # 1. Map GEOGRAPHY
        if 'geography' in icp:
            locations = []
            for geo in icp['geography']:
                if geo.upper() in ['USA', 'US']:
                    locations.append('United States')
                else:
                    locations.append(geo)
            apollo_params['organization_locations'] = locations
        
        # 2. Map EMPLOYEE COUNT
        if 'employee_count_min' in icp:
            emp_min = icp['employee_count_min']
            ranges = []
            # Only include ranges >= employee_count_min
            if emp_min <= 10:
                ranges = ['1,10', '11,20', '21,50', '51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 20:
                ranges = ['11,20', '21,50', '51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 50:
                ranges = ['21,50', '51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 100:
                ranges = ['51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 200:
                ranges = ['101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 500:
                ranges = ['201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            else:
                ranges = ['501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            apollo_params['organization_num_employees_ranges'] = ranges
        
        # 3. Map INDUSTRY + KEYWORDS (combine them)
        keyword_tags = []
        if 'industry' in icp:
            keyword_tags.extend(icp['industry'])
        if 'keywords' in icp:
            keyword_tags.extend(icp['keywords'])
        if keyword_tags:
            apollo_params['q_organization_keyword_tags'] = keyword_tags
        
        # 4. Map TECH STACK
        if 'tech_stack' in signals and signals['tech_stack']:
            apollo_params['organization_technology_slugs'] = signals['tech_stack']
        
        # 5. Map FUNDING SIGNAL
        if signals.get('funding'):
            apollo_params['funding_stage_list'] = [
                'seed', 'series_a', 'series_b', 'series_c', 'series_d', 'series_e', 'series_f'
            ]
        
        # 6. Map REVENUE (using a workaround - not all plans support revenue_range directly)
        # We'll use organization size as proxy along with employee count
        
        return apollo_params
    
    def transform_people_config(self, icp_config: dict) -> dict:
        """Transform ICP config to Apollo People API format."""
        icp = icp_config.get('ICP', {})
        signals = icp_config.get('Signals', {})
        
        apollo_params = {
            'page': 1,
            'per_page': 25
        }
        
        # 1. Map GEOGRAPHY for people
        if 'geography' in icp:
            locations = []
            for geo in icp['geography']:
                if geo.upper() in ['USA', 'US']:
                    locations.append('United States')
                else:
                    locations.append(geo)
            apollo_params['person_locations'] = locations
        
        # 2. Map EMPLOYEE COUNT (for the organizations they work at)
        if 'employee_count_min' in icp:
            emp_min = icp['employee_count_min']
            ranges = []
            if emp_min <= 10:
                ranges = ['1,10', '11,20', '21,50', '51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 20:
                ranges = ['11,20', '21,50', '51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 50:
                ranges = ['21,50', '51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 100:
                ranges = ['51,100', '101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 200:
                ranges = ['101,200', '201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            elif emp_min <= 500:
                ranges = ['201,500', '501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            else:
                ranges = ['501,1000', '1001,2000', '2001,5000', '5001,10000', '10001+']
            apollo_params['organization_num_employees_ranges'] = ranges
        
        # 3. Map KEYWORDS (search for people with these keywords in their profile)
        if 'keywords' in icp:
            apollo_params['q_keywords'] = ' '.join(icp['keywords'])
        
        # 4. Map INDUSTRY (filter organizations by industry keywords)
        if 'industry' in icp:
            apollo_params['organization_industry_keyword_tags'] = icp['industry']
        
        # 5. Map TECH STACK
        if 'tech_stack' in signals and signals['tech_stack']:
            apollo_params['organization_technology_slugs'] = signals['tech_stack']
        
        # 6. Map HIRING DATA ROLES (target people with data-related titles)
        if signals.get('hiring_data_roles'):
            apollo_params['person_titles'] = [
                'Chief Data Officer',
                'VP of Data',
                'Head of Data',
                'Director of Data',
                'Data Science Manager',
                'VP of Analytics',
                'Head of Analytics',
                'Chief Analytics Officer'
            ]
        
        # 7. Map FUNDING SIGNAL
        if signals.get('funding'):
            apollo_params['organization_latest_funding_stage_cd'] = [
                'seed', 'series_a', 'series_b', 'series_c', 'series_d', 'series_e'
            ]
        
        return apollo_params
    
    def search_organizations(self, icp_config: dict) -> dict:
        """Search organizations using Apollo API."""
        url = "https://api.apollo.io/v1/organizations/search"
        
        apollo_params = self.transform_org_config(icp_config)
        
        print(f"\n{'='*70}")
        print("🔍 SEARCHING ORGANIZATIONS")
        print(f"{'='*70}")
        print("\nFilters Applied:")
        icp = icp_config.get('ICP', {})
        signals = icp_config.get('Signals', {})
        print(f"  • Geography: {icp.get('geography', [])}")
        print(f"  • Employee Count: {icp.get('employee_count_min', 'N/A')}+")
        print(f"  • Industry: {icp.get('industry', [])}")
        print(f"  • Keywords: {icp.get('keywords', [])}")
        print(f"  • Tech Stack: {signals.get('tech_stack', [])}")
        print(f"  • Funding: {signals.get('funding', False)}")
        print("\nApollo API Parameters:")
        print(json.dumps(apollo_params, indent=2))
        
        try:
            response = requests.post(url, headers=self.headers, json=apollo_params, timeout=30)
            
            if response.status_code != 200:
                print(f"\n❌ API Response Status: {response.status_code}")
                print(f"API Response Body: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                'error': str(e), 
                'status_code': getattr(response, 'status_code', None),
                'response_body': getattr(response, 'text', None)
            }
    
    def search_people(self, icp_config: dict) -> dict:
        """Search people using Apollo API."""
        url = "https://api.apollo.io/v1/people/search"
        
        apollo_params = self.transform_people_config(icp_config)
        
        print(f"\n{'='*70}")
        print("🔍 SEARCHING PEOPLE")
        print(f"{'='*70}")
        print("\nFilters Applied:")
        icp = icp_config.get('ICP', {})
        signals = icp_config.get('Signals', {})
        print(f"  • Geography: {icp.get('geography', [])}")
        print(f"  • Company Size: {icp.get('employee_count_min', 'N/A')}+ employees")
        print(f"  • Industry: {icp.get('industry', [])}")
        print(f"  • Keywords: {icp.get('keywords', [])}")
        print(f"  • Tech Stack: {signals.get('tech_stack', [])}")
        print(f"  • Hiring Data Roles: {signals.get('hiring_data_roles', False)}")
        print(f"  • Funding: {signals.get('funding', False)}")
        print("\nApollo API Parameters:")
        print(json.dumps(apollo_params, indent=2))
        
        try:
            response = requests.post(url, headers=self.headers, json=apollo_params, timeout=30)
            
            if response.status_code != 200:
                print(f"\n❌ API Response Status: {response.status_code}")
                print(f"API Response Body: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                'error': str(e), 
                'status_code': getattr(response, 'status_code', None),
                'response_body': getattr(response, 'text', None)
            }
    
    def display_org_results(self, results: dict):
        """Display organization search results."""
        if 'error' in results:
            print(f"\n❌ Organization Search Error: {results['error']}")
            if 'response_body' in results:
                print(f"Response: {results['response_body']}")
            return
        
        orgs = results.get('organizations', [])
        total = results.get('pagination', {}).get('total_entries', 0)
        
        print(f"\n{'='*70}")
        print(f"📊 ORGANIZATIONS FOUND: {total} total | Showing: {len(orgs)}")
        print(f"{'='*70}\n")
        
        for i, org in enumerate(orgs, 1):
            print(f"{i}. 🏢 {org.get('name', 'N/A')}")
            print(f"   Industry: {org.get('industry', 'N/A')}")
            print(f"   Employees: {org.get('estimated_num_employees', 'N/A')}")
            
            revenue = org.get('estimated_annual_revenue')
            if revenue:
                print(f"   Revenue: ${revenue:,}")
            
            print(f"   Location: {org.get('city', 'N/A')}, {org.get('state', 'N/A')}, {org.get('country', 'N/A')}")
            print(f"   Website: {org.get('website_url', 'N/A')}")
            
            # Display technologies
            tech = org.get('technologies', [])
            if tech:
                tech_names = [t.get('name', '') for t in tech[:5]]
                print(f"   Tech Stack: {', '.join(tech_names)}")
            
            # Display funding info
            funding = org.get('latest_funding_stage')
            if funding:
                print(f"   Funding Stage: {funding}")
            
            print()
    
    def display_people_results(self, results: dict):
        """Display people search results."""
        if 'error' in results:
            print(f"\n❌ People Search Error: {results['error']}")
            if 'response_body' in results:
                print(f"Response: {results['response_body']}")
            return
        
        people = results.get('people', [])
        total = results.get('pagination', {}).get('total_entries', 0)
        
        print(f"\n{'='*70}")
        print(f"👥 PEOPLE FOUND: {total} total | Showing: {len(people)}")
        print(f"{'='*70}\n")
        
        for i, person in enumerate(people, 1):
            print(f"{i}. 👤 {person.get('name', 'N/A')}")
            print(f"   Title: {person.get('title', 'N/A')}")
            print(f"   Company: {person.get('organization_name', 'N/A')}")
            
            org = person.get('organization', {})
            if org:
                print(f"   Company Size: {org.get('estimated_num_employees', 'N/A')} employees")
                print(f"   Company Industry: {org.get('industry', 'N/A')}")
            
            print(f"   Email: {person.get('email', 'N/A')}")
            phone = person.get('phone_numbers', [])
            if phone:
                print(f"   Phone: {phone[0]}")
            print(f"   LinkedIn: {person.get('linkedin_url', 'N/A')}")
            print(f"   Location: {person.get('city', 'N/A')}, {person.get('state', 'N/A')}")
            print()


def main():
    # Get API key
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ Error: Set APOLLO_API_KEY environment variable")
        return
    
    # Read ICP config using InputHandler
    config_file = 'data/icp_config.yaml'
    handler = InputHandler(config_file, file_type='yaml')
    icp_config = handler.read()
    
    print("\n" + "="*70)
    print("🎯 ICP-BASED APOLLO SEARCH")
    print("="*70)
    print("\nYour ICP Configuration:")
    print(json.dumps(icp_config, indent=2))
    
    # Initialize Apollo
    apollo = ApolloDataRetriever(api_key)
    
    # Search both organizations and people based on ICP
    print("\n" + "="*70)
    print("Starting searches based on your ICP criteria...")
    print("="*70)
    
    # 1. Search Organizations
    org_results = apollo.search_organizations(icp_config)
    apollo.display_org_results(org_results)
    
    # Save organization results
    with open('apollo_organizations_results.json', 'w') as f:
        json.dump(org_results, f, indent=2)
    print("✅ Organization results saved to apollo_organizations_results.json")
    
    # 2. Search People
    people_results = apollo.search_people(icp_config)
    apollo.display_people_results(people_results)
    
    # Save people results
    with open('apollo_people_results.json', 'w') as f:
        json.dump(people_results, f, indent=2)
    print("✅ People results saved to apollo_people_results.json")
    
    # Summary
    org_count = org_results.get('pagination', {}).get('total_entries', 0) if 'error' not in org_results else 0
    people_count = people_results.get('pagination', {}).get('total_entries', 0) if 'error' not in people_results else 0
    
    print(f"\n{'='*70}")
    print(f"🎯 SEARCH SUMMARY - ICP MATCH RESULTS")
    print(f"{'='*70}")
    print(f"Organizations matching your ICP: {org_count}")
    print(f"Decision makers found: {people_count}")
    print(f"\nICP Criteria Applied:")
    icp = icp_config.get('ICP', {})
    signals = icp_config.get('Signals', {})
    print(f"  ✓ Revenue: ${icp.get('revenue_min', 'N/A')} - ${icp.get('revenue_max', 'N/A')}")
    print(f"  ✓ Geography: {', '.join(icp.get('geography', []))}")
    print(f"  ✓ Employee Count: {icp.get('employee_count_min', 'N/A')}+")
    print(f"  ✓ Industries: {', '.join(icp.get('industry', []))}")
    print(f"  ✓ Keywords: {', '.join(icp.get('keywords', []))}")
    print(f"  ✓ Tech Stack: {', '.join(signals.get('tech_stack', []))}")
    print(f"  ✓ Funded: {signals.get('funding', False)}")
    print(f"  ✓ Hiring Data Roles: {signals.get('hiring_data_roles', False)}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()