import httpx
import time

def test_collection_engine():
    print("1. Registering sources...")
    resp = httpx.post("http://127.0.0.1:8000/api/collection/register-all-sources", timeout=300)
    print(f"Status: {resp.status_code}")
    
    print("\n2. Creating test campaign...")
    resp = httpx.post("http://127.0.0.1:8000/api/collection/campaigns?name=Test_Campaign_1&max_urls=20&max_depth=1&max_pages_per_source=2")
    print(f"Status: {resp.status_code}")
    campaign_id = resp.json()["id"]
    print(f"Campaign ID: {campaign_id}")
    
    print("\n3. Running campaign synchronously (limited to 20 URLs)...")
    resp = httpx.post(f"http://127.0.0.1:8000/api/collection/campaigns/{campaign_id}/run", timeout=300)
    print(f"Status: {resp.status_code}")
    
    import json
    print(json.dumps(resp.json(), indent=2))
    
if __name__ == "__main__":
    test_collection_engine()
