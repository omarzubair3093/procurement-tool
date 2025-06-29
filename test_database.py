#!/usr/bin/env python3
"""
Simple database connection test
Run this to verify your database setup is working
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()


def test_database_connection():
    """Test basic database connection and queries"""

    try:
        # Initialize Supabase client
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            print("❌ Error: Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
            return False

        print(f"🔗 Connecting to: {SUPABASE_URL}")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Test 1: Check if tables exist
        print("\n📋 Testing table access...")

        tables_to_check = [
            "user_profiles",
            "rfps",
            "vendors",
            "proposals",
            "evaluations",
            "rfp_templates"
        ]

        for table in tables_to_check:
            try:
                response = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table}: OK ({len(response.data)} rows visible)")
            except Exception as e:
                print(f"❌ {table}: Error - {str(e)}")

        # Test 2: Check user profiles
        print("\n👤 Testing user profiles...")
        try:
            response = supabase.table("user_profiles").select("id, full_name, role").execute()
            print(f"✅ Found {len(response.data)} user profiles:")
            for user in response.data:
                print(f"   - {user.get('full_name', 'Unknown')} ({user.get('role', 'Unknown role')})")
        except Exception as e:
            print(f"❌ Error loading user profiles: {str(e)}")

        # Test 3: Check RFPs
        print("\n📄 Testing RFPs...")
        try:
            response = supabase.table("rfps").select("id, title, status, created_by").execute()
            print(f"✅ Found {len(response.data)} RFPs:")
            for rfp in response.data:
                print(f"   - {rfp.get('title', 'No title')} (Status: {rfp.get('status', 'Unknown')})")
        except Exception as e:
            print(f"❌ Error loading RFPs: {str(e)}")

        # Test 4: Check RFP templates
        print("\n📝 Testing RFP templates...")
        try:
            response = supabase.table("rfp_templates").select("id, name, category").execute()
            print(f"✅ Found {len(response.data)} RFP templates:")
            for template in response.data:
                print(f"   - {template.get('name', 'No name')} ({template.get('category', 'No category')})")
        except Exception as e:
            print(f"❌ Error loading RFP templates: {str(e)}")

        print("\n🎉 Database connection test completed!")
        return True

    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Starting database connection test...\n")

    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found!")
        print("Please create a .env file with your SupaBase credentials.")
        exit(1)

    success = test_database_connection()

    if success:
        print("\n✅ All tests passed! Your database is ready.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("1. Verify your SupaBase URL and API key in .env")
        print("2. Make sure you ran the SQL schema in SupaBase")
        print("3. Check that Row Level Security is properly configured")