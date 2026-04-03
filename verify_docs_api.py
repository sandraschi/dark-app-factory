import requests


def test_specialists_api():
    try:
        response = requests.get("http://localhost:8002/api/specialists")
        data = response.json()
        if data.get("success"):
            print("API Success: Received specialists list")
            for spec in data.get("specialists", []):
                print(f"Specialist: {spec['name']}")
                if "docs" in spec:
                    print(f"  Docs found: {len(spec['docs'])} chars")
                    print(f"  Snippet: {spec['docs'][:50]}...")
                else:
                    print(f"  Error: docs missing for {spec['name']}")
        else:
            print(f"API Failure: {data}")
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    test_specialists_api()
