"""
The search node is responsible for searching for healthcare facilities and medical information.
"""

import os
import json
import requests
import googlemaps
import logging
from typing import cast, Optional, List, Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from copilotkit.langgraph import copilotkit_emit_state, copilotkit_customize_config
from travel.state import AgentState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def search_for_healthcare_facilities(queries: list[str]) -> list[dict]:
    """Search for healthcare facilities based on a query. Returns a list of healthcare facilities including pediatricians, urgent care centers, hospitals, pharmacies, and other medical facilities with their name, address, coordinates, and contact information."""
    facilities = []
    for query in queries:
        try:
            query_facilities = search_healthcare_facilities_api(query)
            facilities.extend(query_facilities)
        except Exception as e:
            logger.error(f"Error searching for healthcare facilities with query '{query}': {e}")

            # Try fallback to legacy Places API first
            gmaps_client = get_gmaps_client()
            fallback_success = False

            if gmaps_client:
                try:
                    # Add healthcare terms to improve legacy search
                    healthcare_query = f"{query} doctor hospital clinic medical"
                    response = gmaps_client.places(healthcare_query)
                    for result in response.get("results", [])[:5]:  # Limit to 5 results per query
                        facility = {
                            "id": result.get("place_id", f"{result.get('name', '')}-{len(facilities)}"),
                            "name": result.get("name", ""),
                            "address": result.get("formatted_address", ""),
                            "latitude": result.get("geometry", {}).get("location", {}).get("lat", 0),
                            "longitude": result.get("geometry", {}).get("location", {}).get("lng", 0),
                            "rating": result.get("rating", 0),
                            "facility_type": "healthcare_facility",
                            "phone": "",
                            "hours": "",
                            "description": "Healthcare Facility"
                        }
                        facilities.append(facility)
                    fallback_success = True
                except Exception as places_error:
                    logger.error(f"Legacy Places API also failed for query '{query}': {places_error}")

            # If legacy Places API failed, try geocoding as final fallback
            if not fallback_success:
                try:
                    geocoding_places = search_places_geocoding_fallback(query)
                    # Convert geocoding results to healthcare facility format
                    for place in geocoding_places:
                        facility = {
                            **place,
                            "facility_type": "healthcare_facility",
                            "phone": "",
                            "hours": "",
                            "description": "Healthcare Facility"
                        }
                        facilities.append(facility)
                except Exception as geocoding_error:
                    logger.error(f"All fallbacks failed for query '{query}': {geocoding_error}")
    return facilities

# Initialize Google Maps client with error handling
def get_gmaps_client() -> Optional[googlemaps.Client]:
    """Get Google Maps client with proper error handling."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY environment variable not set")
        return None
    try:
        return googlemaps.Client(key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Google Maps client: {e}")
        return None

def search_places_mock_fallback(query: str) -> list[dict]:
    """Mock search function that returns sample data when APIs are not available."""
    logger.info(f"Using mock fallback for query: {query}")

    # Generate mock places based on the query
    mock_places = []

    # Extract location from query if possible
    query_lower = query.lower()
    if "new york" in query_lower or "nyc" in query_lower:
        base_lat, base_lng = 40.7128, -74.0060
        city = "New York"
    elif "paris" in query_lower:
        base_lat, base_lng = 48.8566, 2.3522
        city = "Paris"
    elif "london" in query_lower:
        base_lat, base_lng = 51.5074, -0.1278
        city = "London"
    elif "tokyo" in query_lower:
        base_lat, base_lng = 35.6762, 139.6503
        city = "Tokyo"
    else:
        base_lat, base_lng = 40.7128, -74.0060  # Default to NYC
        city = "Unknown City"

    # Generate sample places
    if "restaurant" in query_lower or "food" in query_lower:
        place_types = ["Restaurant", "Cafe", "Bistro", "Diner", "Pizzeria"]
    elif "hotel" in query_lower:
        place_types = ["Hotel", "Inn", "Resort", "Lodge", "Motel"]
    elif "museum" in query_lower:
        place_types = ["Museum", "Gallery", "Exhibition", "Cultural Center", "Art Museum"]
    elif "park" in query_lower:
        place_types = ["Park", "Garden", "Recreation Area", "Nature Reserve", "Plaza"]
    else:
        place_types = ["Location", "Place", "Venue", "Establishment", "Point of Interest"]

    for i in range(5):  # Generate 5 mock places
        # Add small random offset to coordinates
        lat_offset = (i - 2) * 0.01
        lng_offset = (i - 2) * 0.01

        mock_place = {
            "id": f"mock-{i}-{hash(query) % 10000}",
            "name": f"Sample {place_types[i % len(place_types)]} {i+1}",
            "address": f"{100 + i*10} Sample Street, {city}",
            "latitude": base_lat + lat_offset,
            "longitude": base_lng + lng_offset,
            "rating": 4.0 + (i * 0.2),  # Ratings from 4.0 to 4.8
        }
        mock_places.append(mock_place)
        logger.info(f"Generated mock place: {mock_place['name']} at {mock_place['address']}")

    logger.info(f"Mock fallback generated {len(mock_places)} places for query: {query}")
    return mock_places

def search_places_geocoding_fallback(query: str) -> list[dict]:
    """Fallback search using Google Geocoding API when Places API is not available."""
    gmaps_client = get_gmaps_client()
    if not gmaps_client:
        raise ValueError("Google Maps client not available")

    logger.info(f"Using geocoding fallback for query: {query}")

    try:
        # Use geocoding to find locations
        geocode_result = gmaps_client.geocode(query)
        places = []

        for i, result in enumerate(geocode_result[:5]):  # Limit to 5 results to match FIFO queue requirements
            # Extract location info
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})

            place_data = {
                "id": result.get("place_id", f"geocode-{i}"),
                "name": result.get("formatted_address", "").split(",")[0],  # Use first part as name
                "address": result.get("formatted_address", ""),
                "latitude": location.get("lat", 0),
                "longitude": location.get("lng", 0),
                "rating": 0,  # Geocoding doesn't provide ratings
            }
            places.append(place_data)
            logger.info(f"Found location: {place_data['name']} at {place_data['address']}")

        logger.info(f"Geocoding fallback found {len(places)} locations for query: {query}")
        return places

    except Exception as e:
        logger.error(f"Geocoding fallback failed: {e}")
        raise

def search_healthcare_facilities_api(query: str) -> list[dict]:
    """Search for healthcare facilities using the Google Places API (New)"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.types,places.nationalPhoneNumber,places.regularOpeningHours"
    }

    # Enhance query with healthcare-specific terms if not already present
    healthcare_terms = ["doctor", "pediatrician", "hospital", "clinic", "urgent care", "pharmacy", "medical", "health"]
    if not any(term in query.lower() for term in healthcare_terms):
        query = f"{query} healthcare medical"

    data = {
        "textQuery": query,
        "maxResultCount": 5,  # Limit to 5 results per query to match FIFO queue requirements
        "languageCode": "en"
    }

    logger.info(f"Searching for healthcare facilities with query: {query}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        logger.info(f"API Response status: {response.status_code}")

        if response.status_code == 403:
            logger.error("403 Forbidden - Check if Places API (New) is enabled and API key has correct permissions")
            raise requests.exceptions.HTTPError(f"403 Forbidden: Places API (New) access denied. Please check API key permissions.")

        response.raise_for_status()
        result = response.json()
        logger.info(f"API Response: {json.dumps(result, indent=2)}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        raise

    facilities = []
    for place in result.get("places", []):
        # Determine facility type from place types
        place_types = place.get("types", [])
        facility_type = "healthcare_facility"  # default

        if any(t in place_types for t in ["doctor", "hospital"]):
            facility_type = "hospital"
        elif "pharmacy" in place_types:
            facility_type = "pharmacy"
        elif any(t in place_types for t in ["dentist"]):
            facility_type = "dentist"
        elif any(t in place_types for t in ["physiotherapist"]):
            facility_type = "specialist"

        # Extract phone and hours if available
        phone = place.get("nationalPhoneNumber", "")
        hours = ""
        if place.get("regularOpeningHours"):
            hours_data = place.get("regularOpeningHours", {})
            if hours_data.get("weekdayDescriptions"):
                hours = "; ".join(hours_data["weekdayDescriptions"][:2])  # First 2 days

        facility_data = {
            "id": place.get("id", ""),
            "name": place.get("displayName", {}).get("text", "") if place.get("displayName") else "",
            "address": place.get("formattedAddress", ""),
            "latitude": place.get("location", {}).get("latitude", 0),
            "longitude": place.get("location", {}).get("longitude", 0),
            "rating": place.get("rating", 0),
            "facility_type": facility_type,
            "phone": phone,
            "hours": hours,
            "description": f"{facility_type.replace('_', ' ').title()}"
        }
        facilities.append(facility_data)
        logger.info(f"Found healthcare facility: {facility_data['name']} ({facility_type}) at {facility_data['address']}")

    logger.info(f"Found {len(facilities)} healthcare facilities for query: {query}")
    return facilities

def calculate_optimal_map_bounds(facilities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate optimal center point and zoom level for a list of facilities."""
    if not facilities:
        return {"center_latitude": 40.7484, "center_longitude": -73.9857, "zoom_level": 13}

    if len(facilities) == 1:
        # Single facility - center on it with detailed zoom
        facility = facilities[0]
        return {
            "center_latitude": facility["latitude"],
            "center_longitude": facility["longitude"],
            "zoom_level": 15
        }

    # Multiple facilities - calculate bounding box
    latitudes = [f["latitude"] for f in facilities]
    longitudes = [f["longitude"] for f in facilities]

    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lng, max_lng = min(longitudes), max(longitudes)

    # Calculate center point
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2

    # Calculate zoom level based on the span of coordinates
    lat_span = max_lat - min_lat
    lng_span = max_lng - min_lng
    max_span = max(lat_span, lng_span)

    # Determine zoom level based on coordinate span
    if max_span > 0.5:  # Very wide area
        zoom_level = 10
    elif max_span > 0.2:  # Large area
        zoom_level = 11
    elif max_span > 0.1:  # Medium area
        zoom_level = 12
    elif max_span > 0.05:  # Small area
        zoom_level = 13
    elif max_span > 0.02:  # Very small area
        zoom_level = 14
    else:  # Facilities very close together
        zoom_level = 15

    return {
        "center_latitude": center_lat,
        "center_longitude": center_lng,
        "zoom_level": zoom_level
    }

def apply_fifo_facility_limit(existing_facilities: List[Dict[str, Any]], new_facilities: List[Dict[str, Any]], max_facilities: int = 5) -> List[Dict[str, Any]]:
    """Apply FIFO queue logic to maintain maximum facility count."""
    # Combine existing and new facilities
    all_facilities = existing_facilities + new_facilities

    # If we're under the limit, return all facilities
    if len(all_facilities) <= max_facilities:
        return all_facilities

    # If we exceed the limit, keep only the most recent facilities (FIFO)
    # The newest facilities (from new_facilities) take priority
    return all_facilities[-max_facilities:]

async def search_node(state: AgentState, config: RunnableConfig):
    """
    The search node is responsible for searching for healthcare facilities.
    """
    ai_message = cast(AIMessage, state["messages"][-1])

    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "search_progress",
            "tool": "search_for_healthcare_facilities",
            "tool_argument": "search_progress",
        }],
    )

    state["search_progress"] = state.get("search_progress", [])
    queries = ai_message.tool_calls[0]["args"]["queries"]

    for query in queries:
        state["search_progress"].append({
            "query": query,
            "results": [],
            "done": False
        })

    await copilotkit_emit_state(config, state)

    facilities = []
    for i, query in enumerate(queries):
        try:
            # Try the healthcare facilities API first
            query_facilities = search_healthcare_facilities_api(query)
            facilities.extend(query_facilities)
            logger.info(f"Successfully found {len(query_facilities)} healthcare facilities for query '{query}' using new API")
        except Exception as e:
            logger.error(f"Error searching for places with query '{query}' using new API: {e}")

            # Try fallback to legacy Places API first
            gmaps_client = get_gmaps_client()
            fallback_success = False

            if gmaps_client:
                try:
                    logger.info(f"Attempting fallback to legacy Places API for query '{query}'")
                    response = gmaps_client.places(query)
                    fallback_places = []
                    for result in response.get("results", [])[:5]:  # Limit to 5 results
                        place = {
                            "id": result.get("place_id", f"{result.get('name', '')}-{i}"),
                            "name": result.get("name", ""),
                            "address": result.get("formatted_address", ""),
                            "latitude": result.get("geometry", {}).get("location", {}).get("lat", 0),
                            "longitude": result.get("geometry", {}).get("location", {}).get("lng", 0),
                            "rating": result.get("rating", 0),
                        }
                        fallback_places.append(place)
                    facilities.extend(fallback_places)
                    logger.info(f"Successfully found {len(fallback_places)} healthcare facilities for query '{query}' using legacy Places API")
                    fallback_success = True
                except Exception as places_error:
                    logger.error(f"Legacy Places API also failed for query '{query}': {places_error}")

            # If legacy Places API failed, try geocoding as fallback
            if not fallback_success:
                try:
                    logger.info(f"Attempting geocoding fallback for query '{query}'")
                    geocoding_places = search_places_geocoding_fallback(query)
                    facilities.extend(geocoding_places)
                    logger.info(f"Successfully found {len(geocoding_places)} locations for query '{query}' using geocoding")
                    fallback_success = True
                except Exception as geocoding_error:
                    logger.error(f"All Google APIs failed for query '{query}': {geocoding_error}")
                    logger.error("Please enable the Geocoding API in Google Cloud Console")
                    # Re-raise the exception so the user knows there's a configuration issue
                    raise Exception(f"Google Maps APIs not properly configured. Please enable Geocoding API in Google Cloud Console. Original error: {geocoding_error}")

        state["search_progress"][i]["done"] = True
        await copilotkit_emit_state(config, state)

    state["search_progress"] = []
    await copilotkit_emit_state(config, state)

    # Add found facilities to the selected health profile with FIFO queue management
    if facilities and state.get("selected_profile_id"):
        selected_profile_id = state["selected_profile_id"]
        health_profiles = state.get("health_profiles", [])

        for profile in health_profiles:
            if profile["id"] == selected_profile_id:
                # Limit search results to maximum 5 facilities per query
                limited_new_facilities = facilities[:5]

                # Get existing facilities
                existing_facilities = profile.get("facilities", [])

                # Apply FIFO queue logic to maintain 5-facility limit
                updated_facilities = apply_fifo_facility_limit(existing_facilities, limited_new_facilities, max_facilities=5)

                # Update the profile with the new facility list
                profile["facilities"] = updated_facilities

                # Calculate optimal map bounds for all current facilities
                if updated_facilities:
                    map_bounds = calculate_optimal_map_bounds(updated_facilities)
                    profile["center_latitude"] = map_bounds["center_latitude"]
                    profile["center_longitude"] = map_bounds["center_longitude"]
                    profile["zoom_level"] = map_bounds["zoom_level"]

                    logger.info(f"Updated health profile '{profile['child_name']}' with {len(updated_facilities)} facilities (FIFO queue applied)")
                    logger.info(f"Map centered at ({map_bounds['center_latitude']:.4f}, {map_bounds['center_longitude']:.4f}) with zoom level {map_bounds['zoom_level']}")
                else:
                    logger.info(f"No facilities found for health profile '{profile['child_name']}'")

                break

    # Create appropriate success message
    if facilities and state.get("selected_profile_id"):
        selected_profile = next((p for p in state.get("health_profiles", []) if p["id"] == state["selected_profile_id"]), None)
        if selected_profile:
            current_facility_count = len(selected_profile.get("facilities", []))
            message = f"Found {len(facilities)} healthcare facilities and updated the map. Currently showing {current_facility_count} facilities (maximum 5 maintained using FIFO queue). The map has been automatically centered to show all current facilities."
        else:
            message = f"Found {len(facilities)} healthcare facilities but could not update the selected health profile."
    else:
        message = "Search completed but no facilities were found or no health profile is selected."

    state["messages"].append(ToolMessage(
        tool_call_id=ai_message.tool_calls[0]["id"],
        content=message
    ))

    return state
