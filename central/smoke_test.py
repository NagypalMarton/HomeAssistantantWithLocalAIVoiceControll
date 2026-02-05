#!/usr/bin/env python3
"""Smoke test for Central Backend core functionality"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"
HA_BASE_URL = "http://localhost:8001/api/v1"

def test_reg_login_refresh_logout():
    """Test auth flow: register -> login -> refresh -> logout"""
    print("\n=== SMOKE TEST: Auth Flow ===\n")
    
    email = f"smoke_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    
    # Register
    print(f"[1] Register: {email}")
    reg_resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
    })
    assert reg_resp.status_code == 200, f"Register failed: {reg_resp.text}"
    reg_data = reg_resp.json()
    user_id = reg_data["user_id"]
    print(f"    ✓ User created: {user_id}")
    
    # Login
    print(f"[2] Login")
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]
    print(f"    ✓ Access token received (len={len(access_token)})")
    print(f"    ✓ Refresh token received (len={len(refresh_token)})")
    
    # Refresh
    print(f"[3] Refresh token")
    refresh_resp = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert refresh_resp.status_code == 200, f"Refresh failed: {refresh_resp.text}"
    refresh_data = refresh_resp.json()
    new_access_token = refresh_data["access_token"]
    print(f"    ✓ New access token received (len={len(new_access_token)})")
    
    # Logout
    print(f"[4] Logout")
    logout_resp = requests.post(f"{BASE_URL}/auth/logout", json={
        "refresh_token": refresh_token,
    })
    assert logout_resp.status_code == 200, f"Logout failed: {logout_resp.text}"
    print(f"    ✓ Logged out successfully")
    
    return user_id

def test_ha_manager(user_id):
    """Test HA Manager: create instance -> get -> status -> delete"""
    print("\n=== SMOKE TEST: HA Manager ===\n")
    
    # Create
    print(f"[1] Create HA instance for user {user_id[:8]}...")
    create_resp = requests.post(f"{HA_BASE_URL}/ha/instance", json={
        "user_id": user_id,
    })
    assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
    create_data = create_resp.json()
    container_name = create_data["container_name"]
    host_port = create_data["host_port"]
    print(f"    ✓ Instance created: {container_name} (port {host_port})")
    
    # Get
    print(f"[2] Get HA instance")
    get_resp = requests.get(f"{HA_BASE_URL}/ha/instance/{user_id}")
    assert get_resp.status_code == 200, f"Get failed: {get_resp.text}"
    get_data = get_resp.json()
    print(f"    ✓ Instance retrieved: {get_data['container_name']} (status: {get_data['status']})")
    
    # Status
    print(f"[3] Get HA instance status")
    status_resp = requests.get(f"{HA_BASE_URL}/ha/instance/{user_id}/status")
    assert status_resp.status_code == 200, f"Status failed: {status_resp.text}"
    status_data = status_resp.json()
    print(f"    ✓ Status: {status_data['status']}, Health: {status_data['health']}")
    
    # Delete
    print(f"[4] Delete HA instance")
    delete_resp = requests.delete(f"{HA_BASE_URL}/ha/instance/{user_id}")
    assert delete_resp.status_code == 204, f"Delete failed: {delete_resp.text}"
    print(f"    ✓ Instance deleted")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("CENTRAL BACKEND - SMOKE TEST")
        print("=" * 60)
        
        user_id = test_reg_login_refresh_logout()
        test_ha_manager(user_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
