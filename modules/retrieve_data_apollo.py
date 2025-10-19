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
            'X-Api-Key': api_key
        }
    
    def transform_config(self, icp_config: dict) -> dict:
        """Transform ICP config to Apollo API format - FREE TIER ONLY."""
        icp = icp_config.get('ICP', {})
        signals = icp_config.get('Signals', {})
        
        # Only use filters available on FREE tier
        apollo_params = {
            'page': 1,
            'per_page': 10
        }
        
        # Basic keyword search (FREE)
        keywords = []
        if 'industry' in icp:
            keywords.extend(icp['industry'])
        if 'keywords' in icp:
            keywords.extend(icp['keywords'])
        
        if keywords:
            apollo_params['q_organization_keyword_tags'] = keywords
        
        # Location (FREE)
        if 'geography' in icp:
            apollo_params['organization_locations'] = icp['geography']
        
        # NOTE: These are NOT available on free tier:
        # - revenue_range
        # - organization_num_employees_ranges  
        # - organization_technology_slugs
        # - Most advanced filters
        
        return apollo_params
    
    def search(self, icp_config: dict) -> dict:
        """Search Apollo API with ICP config - Free tier friendly."""
        # Use organizations/search for free tier
        url = "https://api.apollo.io/v1/organizations/search"
        
        # Transform config to Apollo format
        apollo_params = self.transform_config(icp_config)
        
        print(f"\nSending to Apollo API:")
        print(json.dumps(apollo_params, indent=2))
        
        try:
            response = requests.post(url, headers=self.headers, json=apollo_params, timeout=30)
            
            # Print detailed error info
            if response.status_code != 200:
                print(f"\nAPI Response Status: {response.status_code}")
                print(f"API Response Body: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e), 'status_code': getattr(response, 'status_code', None)}
    
    def display_results(self, results: dict):
        """Display search results."""
        if 'error' in results:
            print(f"\nError: {results['error']}")
            return
        
        people = results.get('people', [])
        total = results.get('pagination', {}).get('total_entries', 0)
        
        print(f"\n{'='*60}")
        print(f"Found {total} results. Showing {len(people)} people:")
        print(f"{'='*60}\n")
        
        for i, person in enumerate(people, 1):
            print(f"{i}. {person.get('name', 'N/A')}")
            print(f"   Title: {person.get('title', 'N/A')}")
            print(f"   Company: {person.get('organization_name', 'N/A')}")
            print(f"   Email: {person.get('email', 'N/A')}")
            print()


def main():
    # Get API key
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("Error: Set APOLLO_API_KEY environment variable")
        return
    
    # Read ICP config using InputHandler
    config_file = 'data/icp_config.yaml'
    handler = InputHandler(config_file, file_type='yaml')
    icp_config = handler.read()
    
    print("ICP Config loaded:")
    print(json.dumps(icp_config, indent=2))
    
    # Search Apollo
    apollo = ApolloDataRetriever(api_key)
    results = apollo.search(icp_config)
    
    # Display results
    apollo.display_results(results)
    
    # Save results
    with open('apollo_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Results saved to apollo_results.json")


if __name__ == "__main__":
    main()