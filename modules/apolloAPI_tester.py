import requests
import json

# Replace this with your actual API key
API_KEY = "bWD6TaPWZUJyG3IWAzkEbg"

def test_api_health():
    """
    Test if the API key is valid and working
    """
    url = "https://api.apollo.io/v1/auth/health"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": API_KEY
    }
    
    try:
        print("Testing API Key...")
        print("-" * 50)
        
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            # Apollo returns either "healthy" and "is_logged_in" OR just "api_key_valid"
            if (data.get("healthy") and data.get("is_logged_in")) or data.get("api_key_valid"):
                print("\n✅ SUCCESS! Your API key is valid and working!")
                return True
            else:
                print("\n❌ API key validation failed!")
                return False
        else:
            print(f"\n❌ Error: Received status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return False


def test_company_search():
    """
    Test a simple company search to verify API access
    """
    url = "https://api.apollo.io/v1/organizations/search"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": API_KEY
    }
    
    # Simple search payload - searching for companies in tech industry
    payload = {
        "page": 1,
        "per_page": 5,
        "organization_locations": ["United States"],
        "organization_num_employees_ranges": ["1,10"]
    }
    
    try:
        print("\n\nTesting Company Search...")
        print("-" * 50)
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results Found: {data.get('pagination', {}).get('total_entries', 0)}")
            print(f"Results Returned: {len(data.get('organizations', []))}")
            
            # Display first company as example
            if data.get('organizations'):
                first_company = data['organizations'][0]
                print(f"\nExample Company:")
                print(f"  Name: {first_company.get('name', 'N/A')}")
                print(f"  Website: {first_company.get('website_url', 'N/A')}")
                print(f"  Industry: {first_company.get('industry', 'N/A')}")
                
            print("\n✅ Company search working!")
            return True
        else:
            print(f"Response: {response.text}")
            print(f"\n❌ Error: Received status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return False


def test_contact_search():
    """
    Test a simple contact/people search
    """
    url = "https://api.apollo.io/v1/mixed_people/search"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": API_KEY
    }
    
    # Simple search payload - searching for people
    payload = {
        "page": 1,
        "per_page": 5,
        "person_titles": ["CEO", "Founder"],
        "organization_num_employees_ranges": ["1,10"]
    }
    
    try:
        print("\n\nTesting Contact Search...")
        print("-" * 50)
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results Found: {data.get('pagination', {}).get('total_entries', 0)}")
            print(f"Results Returned: {len(data.get('people', []))}")
            
            # Display first contact as example
            if data.get('people'):
                first_person = data['people'][0]
                print(f"\nExample Contact:")
                print(f"  Name: {first_person.get('name', 'N/A')}")
                print(f"  Title: {first_person.get('title', 'N/A')}")
                print(f"  Company: {first_person.get('organization_name', 'N/A')}")
                
            print("\n✅ Contact search working!")
            return True
        else:
            print(f"Response: {response.text}")
            print(f"\n❌ Error: Received status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return False


def search_companies_by_name(company_name):
    """
    Search for a specific company by name
    """
    url = "https://api.apollo.io/v1/organizations/search"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": API_KEY
    }
    
    payload = {
        "page": 1,
        "per_page": 10,
        "q_organization_name": company_name
    }
    
    try:
        print(f"\n\nSearching for companies matching: '{company_name}'")
        print("-" * 50)
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            orgs = data.get('organizations', [])
            
            print(f"Found {len(orgs)} results:\n")
            
            for i, org in enumerate(orgs, 1):
                print(f"{i}. {org.get('name', 'N/A')}")
                print(f"   Website: {org.get('website_url', 'N/A')}")
                print(f"   Industry: {org.get('industry', 'N/A')}")
                print(f"   Employees: {org.get('estimated_num_employees', 'N/A')}")
                print(f"   Location: {org.get('city', '')}, {org.get('state', '')}, {org.get('country', '')}")
                print()
            
            return data
        else:
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("APOLLO.IO API KEY TESTER")
    print("=" * 50)
    
    # Test 1: Check API health
    health_ok = test_api_health()
    
    if health_ok:
        # Test 2: Try company search
        company_search_ok = test_company_search()
        
        # Test 3: Try contact search (may fail on free plan)
        contact_search_ok = test_contact_search()
        
        if not contact_search_ok:
            print("\nℹ️  Note: Contact search requires a paid plan.")
            print("   You can still search for companies and get company details!")
        
        # Test 4: Example - Search for a specific company
        print("\n" + "=" * 50)
        print("BONUS: Search for specific company")
        print("=" * 50)
        search_companies_by_name("Amazon")
    else:
        print("\n⚠️  API key validation failed. Please check your API key and try again.")
    
    print("\n" + "=" * 50)
    print("Testing Complete!")
    print("=" * 50)