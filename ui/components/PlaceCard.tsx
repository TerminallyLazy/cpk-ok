import { Card, CardTitle, CardContent } from "@/components/ui/card";
import { Place, HealthFacility  } from "@/lib/types";
import { Stars } from "@/components/Stars";
import { MapPin, Info, Phone, Clock, Stethoscope } from "lucide-react";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PlaceCardProps = {
  place: Place;
  className?: string;
  number?: number;
  actions?: ReactNode;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
};

export function PlaceCard({ place, actions, onMouseEnter, onMouseLeave, className, number }: PlaceCardProps) {
  // Get facility type icon and color
  const getFacilityIcon = (facilityType?: string) => {
    switch (facilityType) {
      case 'pediatrician':
        return { icon: '👶', color: 'text-green-600' };
      case 'urgent_care':
        return { icon: '🚑', color: 'text-orange-600' };
      case 'hospital':
        return { icon: '🏥', color: 'text-red-600' };
      case 'pharmacy':
        return { icon: '💊', color: 'text-purple-600' };
      case 'dentist':
        return { icon: '🦷', color: 'text-cyan-600' };
      default:
        return { icon: '🏥', color: 'text-blue-600' };
    }
  };

  const facilityInfo = getFacilityIcon(place.facility_type);

  return (
    <Card
      className={cn("hover:shadow-md transition-shadow duration-200", className)}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <CardTitle className="text-xl font-semibold flex items-center gap-2">
                {number && (
                  <div className="text-sm text-background drop-shadow-md bg-foreground rounded-full flex items-center justify-center font-bold border-2 border-white w-7 h-7">
                    {number}
                  </div>
                )}
                <span className={`text-lg ${facilityInfo.color}`}>{facilityInfo.icon}</span>
                {place.name}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Stars rating={place.rating} />
                {place.facility_type && (
                  <span className={`text-xs px-2 py-1 rounded-full bg-gray-100 ${facilityInfo.color} font-medium`}>
                    {place.facility_type.replace('_', ' ').toUpperCase()}
                  </span>
                )}
              </div>
            </div>
            {actions}
          </div>

          <div className="space-y-2 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              <span>{place.address}</span>
            </div>

            {place.phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4" />
                <span>{place.phone}</span>
              </div>
            )}

            {place.hours && (
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>{place.hours}</span>
              </div>
            )}

            {place.description && (
              <div className="flex items-center gap-2 pt-2">
                <Info className="w-4 h-4" />
                <p className="flex-1">{place.description}</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}