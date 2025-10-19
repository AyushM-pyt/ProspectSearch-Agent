import os
import requests
import json
import time
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

        # 3. Map INDUSTRY + KEYWORDS
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

        # 6. Map REVENUE
        if 'revenue_min' in icp or 'revenue_max' in icp:
            rev_min = icp.get('revenue_min', '0')
            rev_max = icp.get('revenue_max', '10B')

            def parse_revenue(val):
                if not val:
                    return None
                val = str(val).upper().replace(',', '').strip()
                if 'B' in val:
                    return int(float(val.replace('B', '')) * 1_000_000_000)
                elif 'M' in val:
                    return int(float(val.replace('M', '')) * 1_000_000)
                elif 'K' in val:
                    return int(float(val.replace('K', '')) * 1_000)
                return int(float(val))

            min_revenue = parse_revenue(rev_min)
            max_revenue = parse_revenue(rev_max)

            apollo_params['_revenue_min'] = min_revenue
            apollo_params['_revenue_max'] = max_revenue

        return apollo_params

    # ------------------- STEP 1: ORGANIZATION SEARCH ------------------- #
    def search_organizations(self, icp_config: dict, max_pages: int = 2) -> dict:
        """Search organizations using Apollo API with pagination."""
        url = "https://api.apollo.io/v1/organizations/search"

        apollo_params = self.transform_org_config(icp_config)

        print(f"\n{'='*70}")
        print("🔍 STEP 1: SEARCHING ORGANIZATIONS")
        print(f"{'='*70}")
        icp = icp_config.get('ICP', {})
        signals = icp_config.get('Signals', {})
        print(f"Filters Applied:")
        print(f"  • Revenue: ${icp.get('revenue_min', 'N/A')} - ${icp.get('revenue_max', 'N/A')}")
        print(f"  • Geography: {icp.get('geography', [])}")
        print(f"  • Employee Count: {icp.get('employee_count_min', 'N/A')}+")
        print(f"  • Industry: {icp.get('industry', [])}")
        print(f"  • Keywords: {icp.get('keywords', [])}")
        print(f"  • Tech Stack: {signals.get('tech_stack', [])}")
        print(f"  • Funding: {signals.get('funding', False)}")

        all_orgs = []
        page = 1

        while page <= max_pages:
            apollo_params['page'] = page
            print(f"\nFetching page {page}...")
            try:
                response = requests.post(url, headers=self.headers, json=apollo_params, timeout=30)

                if response.status_code != 200:
                    print(f"\n❌ API Response Status: {response.status_code}")
                    print(f"Response Body: {response.text}")
                    break

                data = response.json()
                orgs = data.get('organizations', [])
                all_orgs.extend(orgs)
                pagination = data.get('pagination', {})
                total_pages = pagination.get('total_pages', 1)

                print(f"  ✓ Found {len(orgs)} organizations on this page")

                if page >= total_pages or page >= max_pages:
                    break

                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"Error: {e}")
                break

        return {
            'organizations': all_orgs,
            'pagination': {'total_entries': len(all_orgs)}
        }

    # ------------------- STEP 2: PEOPLE ENRICHMENT ------------------- #
    def get_people_from_organization(self, org_id: str, org_name: str, job_titles: list = None) -> list:
        """Get people from a specific organization using mixed_people/search."""
        url = "https://api.apollo.io/v1/mixed_people/search"
        params = {'organization_ids': [org_id], 'page': 1, 'per_page': 10}
        if job_titles:
            params['person_titles'] = job_titles

        try:
            response = requests.post(url, headers=self.headers, json=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('people', [])
            elif response.status_code == 403:
                return self.get_people_alternative(org_id, org_name, job_titles)
            else:
                print(f"⚠️  Could not fetch people for {org_name}: {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️  Error fetching people for {org_name}: {e}")
            return []

    def get_people_alternative(self, org_id: str, org_name: str, job_titles: list = None) -> list:
        """Alternative method using contacts/search endpoint."""
        url = "https://api.apollo.io/v1/contacts/search"
        params = {'organization_ids': [org_id], 'page': 1, 'per_page': 10}
        if job_titles:
            params['titles'] = job_titles
        try:
            response = requests.post(url, headers=self.headers, json=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('contacts', [])
            return []
        except Exception:
            return []

    def enrich_people_from_organizations(self, organizations: list, icp_config: dict) -> list:
        """Extract people from organizations - STEP 2."""
        signals = icp_config.get('Signals', {})
        job_titles = []
        if signals.get('hiring_data_roles'):
            job_titles = [
                'Chief Data Officer', 'VP of Data', 'Head of Data',
                'Director of Data', 'VP of Analytics', 'Head of Analytics',
                'Chief Analytics Officer', 'VP of Engineering', 'CTO'
            ]

        print(f"\n{'='*70}")
        print("🔍 STEP 2: EXTRACTING PEOPLE FROM ORGANIZATIONS")
        print(f"{'='*70}")
        if job_titles:
            print(f"Target Titles: {', '.join(job_titles[:3])}...")

        all_people = []
        for i, org in enumerate(organizations[:10], 1):
            org_id = org.get('id')
            org_name = org.get('name', 'Unknown')
            print(f"{i}. Fetching people from: {org_name}")

            people = self.get_people_from_organization(org_id, org_name, job_titles)
            if people:
                for person in people:
                    person['organization_context'] = {
                        'id': org_id,
                        'name': org_name,
                        'industry': org.get('industry'),
                        'employees': org.get('estimated_num_employees'),
                        'website': org.get('website_url')
                    }
                all_people.extend(people)
                print(f"  ✓ Found {len(people)} people")
            else:
                print(f"  ⚠️  No people found")
            time.sleep(0.5)
        return all_people

    # ------------------- DISPLAY FUNCTIONS ------------------- #
    def display_org_results(self, results: dict):
        """Display organization search results."""
        orgs = results.get('organizations', [])
        print(f"\n{'='*70}")
        print(f"📊 ORGANIZATIONS FOUND: {len(orgs)}")
        print(f"{'='*70}\n")

        for i, org in enumerate(orgs[:10], 1):
            print(f"{i}. 🏢 {org.get('name', 'N/A')}")
            print(f"   Industry: {org.get('industry', 'N/A')}")
            print(f"   Employees: {org.get('estimated_num_employees', 'N/A')}")
            print(f"   Location: {org.get('city', 'N/A')}, {org.get('state', 'N/A')}")
            print(f"   Website: {org.get('website_url', 'N/A')}\n")

    def display_people_results(self, people: list):
        """Display people results."""
        if not people:
            print("⚠️  No people found.")
            return
        print(f"\n{'='*70}")
        print(f"👥 PEOPLE FOUND: {len(people)}")
        print(f"{'='*70}\n")
        for i, p in enumerate(people[:10], 1):
            print(f"{i}. 👤 {p.get('name', 'N/A')} | {p.get('title', 'N/A')} | {p.get('organization_context', {}).get('name', 'N/A')}")


def main():
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ Error: Set APOLLO_API_KEY in .env file")
        return

    config_file = 'data/icp_config.yaml'
    handler = InputHandler(config_file, file_type='yaml')
    icp_config = handler.read()

    print("\n🎯 ICP-BASED APOLLO SEARCH (2-STEP WORKFLOW)")
    apollo = ApolloDataRetriever(api_key)

    org_results = apollo.search_organizations(icp_config)
    apollo.display_org_results(org_results)

    organizations = org_results.get('organizations', [])
    if organizations:
        people = apollo.enrich_people_from_organizations(organizations, icp_config)
        apollo.display_people_results(people)
    else:
        print("\n⚠️ No organizations found.")


if __name__ == "__main__":
    main()
