#!/usr/bin/env python3
"""
Test script to verify Google Maps API configuration and functionality.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the travel module to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from travel.search import search_healthcare_facilities_api, get_gmaps_client, search_places_geocoding_fallback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_key():
    """Test if API key is properly configured."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_MAPS_API_KEY environment variable not set")
        return False

    logger.info(f"✅ API key found: {api_key[:10]}...")
    return True

def test_healthcare_facilities_api():
    """Test the healthcare facilities API."""
    logger.info("Testing healthcare facilities API...")

    try:
        # Test with a healthcare query
        test_query = "pediatricians in New York"
        facilities = search_healthcare_facilities_api(test_query)

        if facilities:
            logger.info(f"✅ Healthcare facilities API working! Found {len(facilities)} facilities")
            for i, facility in enumerate(facilities[:3]):  # Show first 3 results
                logger.info(f"  {i+1}. {facility['name']} ({facility.get('facility_type', 'N/A')}) - {facility['address']}")
            return True
        else:
            logger.warning("⚠️ Healthcare facilities API returned no results")
            return False

    except Exception as e:
        logger.error(f"❌ Healthcare facilities API failed: {e}")
        return False

def test_legacy_api():
    """Test the legacy Google Maps API."""
    logger.info("Testing legacy Google Maps API...")

    try:
        gmaps_client = get_gmaps_client()
        if not gmaps_client:
            logger.error("❌ Could not initialize Google Maps client")
            return False

        # Test with a simple query
        test_query = "restaurants in New York"
        response = gmaps_client.places(test_query)

        if response and response.get("results"):
            places = response["results"]
            logger.info(f"✅ Legacy API working! Found {len(places)} places")
            for i, place in enumerate(places[:3]):  # Show first 3 results
                logger.info(f"  {i+1}. {place.get('name', 'Unknown')} - {place.get('formatted_address', 'No address')}")
            return True
        else:
            logger.warning("⚠️ Legacy API returned no results")
            return False

    except Exception as e:
        logger.error(f"❌ Legacy API failed: {e}")
        return False

def test_geocoding_fallback():
    """Test the geocoding fallback API."""
    logger.info("Testing geocoding fallback API...")

    try:
        # Test with a simple query
        test_query = "restaurants in New York"
        places = search_places_geocoding_fallback(test_query)

        if places:
            logger.info(f"✅ Geocoding fallback working! Found {len(places)} locations")
            for i, place in enumerate(places[:3]):  # Show first 3 results
                logger.info(f"  {i+1}. {place['name']} - {place['address']}")
            return True
        else:
            logger.warning("⚠️ Geocoding fallback returned no results")
            return False

    except Exception as e:
        logger.error(f"❌ Geocoding fallback failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting Google Maps API tests...")

    # Test API key configuration
    if not test_api_key():
        logger.error("❌ API key test failed. Please check your .env file.")
        return False

    # Test healthcare facilities API
    healthcare_api_works = test_healthcare_facilities_api()

    # Test legacy API
    legacy_api_works = test_legacy_api()

    # Test geocoding fallback
    geocoding_works = test_geocoding_fallback()

    # Summary
    logger.info("\n📊 Test Summary:")
    logger.info(f"  Healthcare Facilities API: {'✅ Working' if healthcare_api_works else '❌ Failed'}")
    logger.info(f"  Legacy Places API: {'✅ Working' if legacy_api_works else '❌ Failed'}")
    logger.info(f"  Geocoding Fallback: {'✅ Working' if geocoding_works else '❌ Failed'}")

    if healthcare_api_works or legacy_api_works or geocoding_works:
        logger.info("🎉 At least one API is working! The healthcare search functionality should work.")
        return True
    else:
        logger.error("💥 All APIs failed. Please check your API key and enabled services.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
