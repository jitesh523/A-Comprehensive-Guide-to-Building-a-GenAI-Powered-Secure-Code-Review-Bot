"""
Test script for webhook integration
"""
import requests
import hmac
import hashlib
import json


def test_webhook_signature():
    """Test HMAC signature validation"""
    print("=" * 60)
    print("Testing Webhook Signature Validation")
    print("=" * 60)
    
    # Test payload
    payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "number": 1,
            "head": {"sha": "abc123"}
        },
        "repository": {
            "full_name": "test/repo"
        }
    }
    
    payload_bytes = json.dumps(payload).encode()
    
    # Compute signature
    secret = "test_secret".encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    
    print(f"\n✅ Payload: {json.dumps(payload, indent=2)[:100]}...")
    print(f"✅ Signature: sha256={signature}")
    
    # Send request
    url = "http://localhost:8000/webhook/github"
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": f"sha256={signature}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📡 Response Body: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ Webhook test passed!")
        else:
            print(f"\n❌ Webhook test failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n⚠️  Server not running. Start with: docker-compose up")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def test_ping_event():
    """Test ping event"""
    print("\n" + "=" * 60)
    print("Testing Ping Event")
    print("=" * 60)
    
    payload = {"zen": "Design for failure."}
    payload_bytes = json.dumps(payload).encode()
    
    secret = "test_secret".encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    
    url = "http://localhost:8000/webhook/github"
    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": f"sha256={signature}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\n📡 Response: {response.json()}")
        
        if response.json().get("message") == "pong":
            print("✅ Ping test passed!")
        else:
            print("❌ Ping test failed!")
            
    except requests.exceptions.ConnectionError:
        print("\n⚠️  Server not running")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    print("\n🔗 Webhook Integration Test Suite")
    print("=" * 60)
    print("\nNote: Ensure server is running (docker-compose up)")
    print("      and GITHUB_WEBHOOK_SECRET is set in .env\n")
    
    test_webhook_signature()
    test_ping_event()
    
    print("\n" + "=" * 60)
    print("✅ Webhook tests complete!")
    print("=" * 60)
