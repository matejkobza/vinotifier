#!/usr/bin/env python3
"""
Check myVAILLANT API connection.
Tests if credentials and connection to myVAILLANT API are working.
"""

import asyncio
import os
import sys
from myPyllant.api import MyPyllantAPI

async def check_connection():
    """Test connection to myVAILLANT API."""

    # Get environment variables
    user = os.getenv("MYVAILLANT_USER")
    password = os.getenv("MYVAILLANT_PASS")
    country = os.getenv("MYVAILLANT_COUNTRY", "germany")
    brand = os.getenv("MYVAILLANT_BRAND", "vaillant")

    # Validate environment variables
    if not user or not password:
        print("❌ Error: MYVAILLANT_USER or MYVAILLANT_PASS not set")
        sys.exit(1)

    print(f"🔍 Testing myVAILLANT connection...")
    print(f"   User: {user}")
    print(f"   Country: {country}")
    print(f"   Brand: {brand}")
    print()

    try:
        async with MyPyllantAPI(
            username=user,
            password=password,
            country=country,
            brand=brand
        ) as api:
            print("✅ Successfully connected to myVAILLANT API")

            # Try to fetch systems
            try:
                systems = await api.get_systems()
                print(f"✅ Successfully fetched {len(systems)} system(s)")

                for system in systems:
                    print(f"   - System: {system.id}")
                    zones = await api.get_zones(system.id)
                    print(f"     Zones: {len(zones)}")

                print("\n✅ Connection test passed!")
                return True

            except Exception as e:
                print(f"❌ Error fetching systems: {e}")
                return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_connection())
    sys.exit(0 if success else 1)

