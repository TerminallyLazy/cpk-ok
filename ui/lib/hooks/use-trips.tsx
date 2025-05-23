import { SearchProgress } from "@/components/SearchProgress";
import { useCoAgent, useCoAgentStateRender, useCopilotAction } from "@copilotkit/react-core";
import { useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { createContext, useContext, ReactNode, useMemo, useEffect, useState } from "react";
import { AddTrips, EditTrips, DeleteTrips } from "@/components/humanInTheLoop";
import { Trip, Place, AgentState, defaultTrips, HealthProfile, HealthFacility, defaultHealthProfiles} from "@/lib/types";
import { useGeolocation, getDefaultLocation } from "@/lib/hooks/use-geolocation";

type TripsContextType = {
  trips: Trip[];
  selectedTripId: string | null;
  selectedTrip?: Trip | null;
  setSelectedTripId: (trip_id: string | null) => void;
  addTrip: (trip: Trip) => void;
  updateTrip: (id: string, updatedTrip: Trip) => void;
  deleteTrip: (id: string) => void;
  addPlace: (tripId: string, place: Place) => void;
  updatePlace: (tripId: string, placeId: string, updatedPlace: Place) => void;
  deletePlace: (tripId: string, placeId: string) => void;
};

const TripsContext = createContext<TripsContextType | undefined>(undefined);

export const TripsProvider = ({ children }: { children: ReactNode }) => {
  // Get user's current location
  const geolocation = useGeolocation({
    enableHighAccuracy: false,
    timeout: 10000,
    maximumAge: 300000, // 5 minutes
  });

  // State for location notification
  const [locationNotification, setLocationNotification] = useState<{
    message: string;
    type: 'success' | 'error' | null;
  }>({ message: '', type: null });

  const { state, setState } = useCoAgent<AgentState>({
    name: "healthcare",
    initialState: {
      health_profiles: defaultHealthProfiles,
      selected_profile_id: defaultHealthProfiles[0].id,
      // Keep legacy fields for backward compatibility
      trips: defaultTrips,
      selected_trip_id: defaultTrips[0].id,
    },
  });

  useCoAgentStateRender<AgentState>({
    name: "healthcare",
    render: ({ state }) => {
      if (state.search_progress && state.search_progress.length > 0) {
        return <SearchProgress progress={state.search_progress} />
      }

      // Show location detection status
      if (geolocation.loading) {
        return (
          <div className="fixed top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Detecting your location...</span>
            </div>
          </div>
        );
      }

      // Show location notification
      if (locationNotification.type) {
        const bgColor = locationNotification.type === 'success' ? 'bg-green-500' : 'bg-red-500';
        return (
          <div className={`fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded-lg shadow-lg z-50`}>
            <div className="flex items-center gap-2">
              <span>{locationNotification.message}</span>
            </div>
          </div>
        );
      }

      return null;
    },
  });

  // Update health profiles with user's current location when geolocation is available
  useEffect(() => {
    if (!geolocation.loading && (geolocation.latitude !== null && geolocation.longitude !== null)) {
      // User location detected successfully
      const updatedProfiles = state.health_profiles.map(profile => ({
        ...profile,
        center_latitude: geolocation.latitude!,
        center_longitude: geolocation.longitude!,
      }));

      const updatedTrips = state.trips.map(trip => ({
        ...trip,
        center_latitude: geolocation.latitude!,
        center_longitude: geolocation.longitude!,
      }));

      setState({
        ...state,
        health_profiles: updatedProfiles,
        trips: updatedTrips,
      });

      // Show success notification
      setLocationNotification({
        message: 'Location detected successfully!',
        type: 'success'
      });

      console.log(`Location detected: ${geolocation.latitude}, ${geolocation.longitude}`);
    } else if (!geolocation.loading && geolocation.error) {
      // Geolocation failed, use default location
      const defaultLocation = getDefaultLocation();
      const updatedProfiles = state.health_profiles.map(profile => ({
        ...profile,
        center_latitude: defaultLocation.latitude,
        center_longitude: defaultLocation.longitude,
      }));

      const updatedTrips = state.trips.map(trip => ({
        ...trip,
        center_latitude: defaultLocation.latitude,
        center_longitude: defaultLocation.longitude,
      }));

      setState({
        ...state,
        health_profiles: updatedProfiles,
        trips: updatedTrips,
      });

      // Show error notification
      setLocationNotification({
        message: 'Using default location (NYC)',
        type: 'error'
      });

      console.log(`Geolocation failed (${geolocation.error}), using default location: ${defaultLocation.latitude}, ${defaultLocation.longitude}`);
    }
  }, [geolocation.loading, geolocation.latitude, geolocation.longitude, geolocation.error]);

  // Auto-hide location notification after 3 seconds
  useEffect(() => {
    if (locationNotification.type) {
      const timer = setTimeout(() => {
        setLocationNotification({ message: '', type: null });
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [locationNotification.type]);

  useCopilotChatSuggestions({
    instructions: `Offer the user actionable suggestions on their last message, current health profiles and selected profile. Focus on healthcare-related suggestions like finding pediatricians, urgent care, or answering health questions.\n Selected Profile: ${state.selected_profile_id} \n Health Profiles: ${JSON.stringify(state.health_profiles)}`,
    minSuggestions: 1,
    maxSuggestions: 2,
  }, [state.health_profiles]);

  useCopilotAction({
    name: "add_health_profiles",
    description: "Add health profiles for children",
    parameters: [
      {
        name: "health_profiles",
        type: "object[]",
        description: "The health profiles to add",
        required: true,
      },
    ],
    renderAndWait: AddTrips, // Reuse component for now, will update later
  });

  useCopilotAction({
    name: "update_health_profiles",
    description: "Update health profiles for children",
    parameters: [
      {
        name: "health_profiles",
        type: "object[]",
        description: "The health profiles to update",
        required: true,
      },
    ],
    renderAndWait: EditTrips, // Reuse component for now, will update later
  });

  useCopilotAction({
    name: "delete_health_profiles",
    description: "Delete health profiles for children",
    parameters: [
      {
        name: "profile_ids",
        type: "string[]",
        description: "The ids of the health profiles to delete",
        required: true,
      },
    ],
    renderAndWait: (props) => DeleteTrips({ ...props, trips: state.trips }), // Reuse component for now
  });

  // Keep legacy actions for backward compatibility
  useCopilotAction({
    name: "add_trips",
    description: "Add some trips",
    parameters: [
      {
        name: "trips",
        type: "object[]",
        description: "The trips to add",
        required: true,
      },
    ],
    renderAndWait: AddTrips,
  });

  useCopilotAction({
    name: "update_trips",
    description: "Update some trips",
    parameters: [
      {
        name: "trips",
        type: "object[]",
        description: "The trips to update",
        required: true,
      },
    ],
    renderAndWait: EditTrips,
  });

  useCopilotAction({
    name: "delete_trips",
    description: "Delete some trips",
    parameters: [
      {
        name: "trip_ids",
        type: "string[]",
        description: "The ids of the trips to delete",
        required: true,
      },
    ],
    renderAndWait: (props) => DeleteTrips({ ...props, trips: state.trips }),
  });

  const selectedTrip = useMemo(() => {
    // First try to use health profiles (new system)
    if (state.selected_profile_id && state.health_profiles) {
      const selectedProfile = state.health_profiles.find((profile) => profile.id === state.selected_profile_id);
      if (selectedProfile) {
        // Convert health profile to trip format for backward compatibility
        return {
          id: selectedProfile.id,
          name: `${selectedProfile.child_name}'s Healthcare`,
          center_latitude: selectedProfile.center_latitude,
          center_longitude: selectedProfile.center_longitude,
          zoom_level: selectedProfile.zoom_level || 13,
          places: selectedProfile.facilities || [],
          notes: selectedProfile.notes,
        };
      }
    }

    // Fallback to legacy trips system
    if (!state.selected_trip_id || !state.trips) return null;
    return state.trips.find((trip) => trip.id === state.selected_trip_id);
  }, [state.health_profiles, state.selected_profile_id, state.trips, state.selected_trip_id]);

  /*
  * Helper functions for trips
  */
  const addTrip = (trip: Trip) => {
    setState({ ...state, trips: [...state.trips, trip]});
  };

  const updateTrip = (id: string, updatedTrip: Trip) => {
    setState({
      ...state,
      trips: state.trips.map((trip) =>
        trip.id === id ? updatedTrip : trip
      ),
    });
  };

  const deleteTrip = (id: string) => {
    setState({ ...state, trips: state.trips.filter((trip) => trip.id !== id) });
  };

  const setSelectedTripId = (trip_id: string | null) => {
    // Update both health profile selection and legacy trip selection for compatibility
    setState({
      ...state,
      selected_profile_id: trip_id,
      selected_trip_id: trip_id
    });
  };

  /*
  * Helper functions for places
  */
  const updatePlace = (tripId: string, placeId: string, updatedPlace: Place) => {
    // Update health profiles if using new system
    if (state.health_profiles && state.selected_profile_id === tripId) {
      setState({
        ...state,
        health_profiles: state.health_profiles.map((profile) =>
          profile.id === tripId
            ? {
                ...profile,
                facilities: (profile.facilities || []).map((facility) =>
                  facility.id === placeId ? updatedPlace : facility
                )
              }
            : profile
        ),
      });
    } else {
      // Fallback to legacy trips system
      setState({
        ...state,
        trips: state.trips.map((trip) =>
          trip.id === tripId ? { ...trip, places: trip.places.map((place) => place.id === placeId ? updatedPlace : place) } : trip
        ),
      });
    }
  };

  const addPlace = (tripId: string, place: Place) => {
    // Update health profiles if using new system
    if (state.health_profiles && state.selected_profile_id === tripId) {
      setState({
        ...state,
        health_profiles: state.health_profiles.map((profile) =>
          profile.id === tripId
            ? { ...profile, facilities: [...(profile.facilities || []), place] }
            : profile
        ),
      });
    } else {
      // Fallback to legacy trips system
      setState({
        ...state,
        trips: state.trips.map((trip) => trip.id === tripId ? { ...trip, places: [...trip.places, place] } : trip),
      });
    }
  };

  const deletePlace = (tripId: string, placeId: string) => {
    // Update health profiles if using new system
    if (state.health_profiles && state.selected_profile_id === tripId) {
      setState({
        ...state,
        health_profiles: state.health_profiles.map((profile) =>
          profile.id === tripId
            ? { ...profile, facilities: (profile.facilities || []).filter((facility) => facility.id !== placeId) }
            : profile
        ),
      });
    } else {
      // Fallback to legacy trips system
      setState({
        ...state,
        trips: state.trips.map((trip) => trip.id === tripId ? { ...trip, places: trip.places.filter((place) => place.id !== placeId) } : trip),
      });
    }
  };

  // Convert health profiles to trips for the UI
  const tripsFromProfiles = useMemo(() => {
    if (state.health_profiles) {
      return state.health_profiles.map(profile => ({
        id: profile.id,
        name: `${profile.child_name}'s Healthcare`,
        center_latitude: profile.center_latitude,
        center_longitude: profile.center_longitude,
        zoom_level: profile.zoom_level || 13,
        places: profile.facilities || [],
        notes: profile.notes,
      }));
    }
    return [];
  }, [state.health_profiles]);

  // Use health profiles as trips, fallback to legacy trips
  const allTrips = tripsFromProfiles.length > 0 ? tripsFromProfiles : state.trips;

  return (
    <TripsContext.Provider value={{
      trips: allTrips,
      selectedTripId: state.selected_profile_id || state.selected_trip_id,
      selectedTrip,
      setSelectedTripId,
      addTrip,
      updateTrip,
      deleteTrip,
      addPlace,
      updatePlace,
      deletePlace,
    }}>
      {children}
    </TripsContext.Provider>
  );
};

export const useTrips = () => {
  const context = useContext(TripsContext);
  if (context === undefined) {
    throw new Error("useTrips must be used within a TripsProvider");
  }
  return context;
};