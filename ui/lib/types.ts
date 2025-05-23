export type HealthFacility = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  rating: number;
  description?: string;
  facility_type?: string; // e.g., "pediatrician", "urgent_care", "hospital", "pharmacy"
  phone?: string;
  hours?: string;
};

export type HealthProfile = {
  id: string;
  child_name: string;
  age?: number;
  center_latitude: number;
  center_longitude: number;
  zoom_level?: number | 13;
  facilities: HealthFacility[];
  notes?: string; // Health notes, allergies, etc.
};

export type SearchProgress = {
  query: string;
  done: boolean;
};

export type AgentState = {
  health_profiles: HealthProfile[];
  selected_profile_id: string | null;
  // Legacy trips fields for backward compatibility
  trips: Trip[];
  selected_trip_id: string | null;
  search_progress?: SearchProgress[];
};

// Keep legacy types for backward compatibility during transition
export type Place = HealthFacility;
export type Trip = Omit<HealthProfile, 'child_name' | 'age' | 'facilities'> & {
  name: string;
  places: Place[];
  notes?: string;
};

export const defaultHealthProfiles: HealthProfile[] = [
  {
    id: "1",
    child_name: "Emma",
    age: 5,
    center_latitude: 40.7484,
    center_longitude: -73.9857,
    facilities: [], // Start with empty facilities - will be populated by search
    zoom_level: 13,
    notes: "Allergic to peanuts. Regular checkups every 6 months."
  },
  {
    id: "2",
    child_name: "Liam",
    age: 8,
    center_latitude: 40.7589,
    center_longitude: -73.9851,
    facilities: [], // Start with empty facilities - will be populated by search
    zoom_level: 13,
    notes: "Asthma - carries inhaler. Annual sports physical required."
  },
];

// Keep legacy default for backward compatibility
export const defaultTrips: Trip[] = defaultHealthProfiles.map(profile => ({
  id: profile.id,
  name: `${profile.child_name}'s Healthcare`,
  center_latitude: profile.center_latitude,
  center_longitude: profile.center_longitude,
  zoom_level: profile.zoom_level,
  places: profile.facilities,
  notes: profile.notes
}));