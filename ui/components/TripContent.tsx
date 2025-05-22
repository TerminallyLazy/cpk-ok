import { Trip, HealthProfile } from "@/lib/types";
import { Map } from "leaflet";
import { PlaceForMap } from "@/components/PlaceForMap";
import { AddPlace } from "./AddPlace";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { User, Calendar, FileText, MapPin } from "lucide-react";

export type TripContentProps = {
  map?: Map;
  trip: Trip;
}

export function TripContent({ map, trip }: TripContentProps) {
  if (!trip) return null;

  // Extract child info from trip name (temporary until we have proper health profile data)
  const childName = trip.name.replace("'s Healthcare", "");

  return (
    <div className="flex flex-col gap-4">
      {/* Child Information Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <User className="w-5 h-5 text-blue-600" />
            {childName}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex flex-wrap gap-2 mb-3">
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              <MapPin className="w-3 h-3 mr-1" />
              {trip.places?.length || 0} Healthcare Facilities
            </Badge>
          </div>

          {/* Notes Section - This will be populated by the agent */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <FileText className="w-4 h-4" />
              Health Notes
            </div>
            <div className="text-sm text-gray-600 bg-white p-3 rounded-md border">
              <p className="italic">
                Health notes and information will appear here as you interact with the assistant.
                Ask me about your child's health, allergies, or medical history!
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add Healthcare Facility Button */}
      {map && (
        <div className="flex justify-center">
          <AddPlace map={map} />
        </div>
      )}

      {/* Healthcare Facilities List */}
      <div className="space-y-3">
        {trip.places && trip.places.length > 0 && (
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Healthcare Facilities
          </h3>
        )}
        {trip.places && trip.places.map((place, i) => (
          <PlaceForMap key={i} place={place} map={map} number={i + 1} />
        ))}
      </div>
    </div>
  );
}
