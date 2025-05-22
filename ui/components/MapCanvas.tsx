import { MapContainer, TileLayer, Marker, Tooltip } from "react-leaflet";
import { useTrips } from "@/lib/hooks/use-trips";
import { useEffect, useState, useRef } from "react";
import { Map, divIcon } from "leaflet";
import { cn } from "@/lib/utils";
import { TripCard } from "@/components/TripCard";
import { PlaceCard } from "@/components/PlaceCard";
import { useMediaQuery } from "@/lib/hooks/use-media-query";
import { MobileTripCard } from "./MobileTripCard";
import { useChatContext } from "@copilotkit/react-ui";

export type MapCanvasProps = {
  className?: string;
}

export function MapCanvas({ className }: MapCanvasProps) {
	const [map, setMap] = useState<Map | null>(null);
	const { selectedTrip } = useTrips();
  const { setOpen } = useChatContext();
  const isDesktop = useMediaQuery("(min-width: 900px)");
  const prevIsDesktop = useRef(isDesktop);

  useEffect(() => {
    if (prevIsDesktop.current !== isDesktop) {
      setOpen(isDesktop);
    }
    prevIsDesktop.current = isDesktop;
  }, [isDesktop, setOpen]);

  return (
		<div className="">
			<MapContainer
				className={cn("w-screen h-screen", className)}
				style={{ zIndex: 0 }}
				center={[0, 0]}
				zoom={1}
				zoomAnimationThreshold={100}
				zoomControl={false}
				ref={setMap}
			>
				<TileLayer
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
				/>
      {selectedTrip && selectedTrip.places.map((place, i) => {
        // Determine icon based on facility type
        const facilityType = place.facility_type || 'healthcare_facility';
        let iconColor = 'bg-blue-500'; // default healthcare color
        let iconSymbol = '🏥'; // default healthcare symbol

        switch (facilityType) {
          case 'pediatrician':
            iconColor = 'bg-green-500';
            iconSymbol = '👶';
            break;
          case 'urgent_care':
            iconColor = 'bg-orange-500';
            iconSymbol = '🚑';
            break;
          case 'hospital':
            iconColor = 'bg-red-500';
            iconSymbol = '🏥';
            break;
          case 'pharmacy':
            iconColor = 'bg-purple-500';
            iconSymbol = '💊';
            break;
          case 'dentist':
            iconColor = 'bg-cyan-500';
            iconSymbol = '🦷';
            break;
          default:
            iconColor = 'bg-blue-500';
            iconSymbol = '🏥';
        }

        return (
          <Marker
            key={i}
            position={[place.latitude, place.longitude]}
            icon={divIcon({
              className: "bg-transparent",
              html: `<div class="${iconColor} text-white w-10 h-10 rounded-full flex items-center justify-center font-bold border-2 border-white shadow-lg text-lg">${iconSymbol}</div>`,
              iconSize: [40, 40],
              iconAnchor: [20, 20],
            })}
          >
            <Tooltip offset={[10, 0]} opacity={1}>
              <PlaceCard className="border-none overflow-y-auto shadow-none" place={place} />
            </Tooltip>
          </Marker>
        );
      })}
      </MapContainer>
      {map &&
        <>
          {isDesktop ? (
            <div className="absolute h-screen top-0 p-10 pointer-events-none flex items-start w-[25%] md:w-[35%] lg:w-[30%] 2xl:w-[25%]">
              <TripCard
                className="w-full h-full pointer-events-auto"
                map={map}
              />
            </div>
          ) : (
            <MobileTripCard className="w-full h-full pointer-events-auto" map={map} />
          )}
        </>
      }
		</div>
  );
}
