# Google Maps API Setup Guide

## Current Issue

The travel agent is failing because the Google Maps API key doesn't have the required APIs enabled. Here's what's happening:

1. **New Places API (403 Forbidden)**: The Places API (New) is not enabled for your project
2. **Legacy Places API (REQUEST_DENIED)**: Legacy APIs are disabled for your project  
3. **Geocoding API (REQUEST_DENIED)**: The Geocoding API is not enabled for your project

## Solution: Enable Required APIs

### Step 1: Go to Google Cloud Console

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Go to "APIs & Services" > "Library"

### Step 2: Enable Required APIs

Search for and enable these APIs:

#### Required APIs:
1. **Places API (New)** - For modern place searches
   - Search for "Places API (New)"
   - Click "Enable"

2. **Geocoding API** - For address/location lookups (fallback)
   - Search for "Geocoding API" 
   - Click "Enable"

#### Optional APIs (for better functionality):
3. **Places API** - Legacy fallback
   - Search for "Places API"
   - Click "Enable"

4. **Maps JavaScript API** - For frontend map display
   - Search for "Maps JavaScript API"
   - Click "Enable"

### Step 3: Configure API Key Restrictions (Recommended)

1. Go to "APIs & Services" > "Credentials"
2. Click on your API key
3. Under "API restrictions", select "Restrict key"
4. Choose the APIs you enabled above
5. Save changes

### Step 4: Test the Configuration

Run the test script to verify everything works:

```bash
cd agent
python test_google_maps.py
```

## Alternative: Use a Different API Key

If you can't modify the current project, you can:

1. Create a new Google Cloud project
2. Enable the required APIs
3. Create a new API key
4. Update your `.env` file with the new key

## Temporary Workaround

If you can't enable the APIs right now, I've implemented a mock search that returns sample data. This allows the application to work while you configure the APIs.

## Cost Considerations

- **Places API (New)**: $0.032 per request (first 100,000 requests per month)
- **Geocoding API**: $0.005 per request (first 40,000 requests per month)
- **Places API (Legacy)**: $0.032 per request

For development/testing, these costs are minimal.

## Next Steps

1. Enable the APIs in Google Cloud Console
2. Test with `python test_google_maps.py`
3. Once working, restart your travel agent application

The application should work immediately after enabling the APIs - no code changes needed!
