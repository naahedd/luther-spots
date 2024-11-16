import React, { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface dataFormat {
    building: string;
    building_code: string;
    building_status: string;
    rooms: {
        [key: string]: {
            roomNumber: string;
            slots: { StartTime: string; EndTime: string; Status: string }[];
        };
    };
    coords: [number, number];
    distance: number;
}

export default function Map({
    data,
    handleMarkerClick,
    userPos,
}: {
    data: dataFormat[];
    handleMarkerClick: (building: string) => void;
    userPos: [number, number] | null;
}) {
    const mapRef = useRef<mapboxgl.Map | null>(null);
    const mapContainerRef = useRef<HTMLDivElement | null>(null);

    const [center] = useState<[number, number]>([-91.803, 43.3125]);
    const [zoom] = useState(16.50)
    const [pitch] = useState(52);
    const [bearing] = useState(40);

    const mapboxToken = "pk.eyJ1IjoiZWxnaG91bCIsImEiOiJjbTNkdWd1cWYwN3piMmtwcWFmcTVvanU2In0.dGrQb79ZD8CeUQeoWNfGcg";

    function getColorByStatus(status: string) {
        switch (status) {
            case "available":
                return "h-2 w-2 rounded-full bg-green-400 shadow-[0px_0px_4px_2px_rgba(34,197,94,0.7)]";
            case "unavailable":
                return "h-2 w-2 rounded-full bg-red-400 shadow-[0px_0px_4px_2px_rgba(239,68,68,0.9)]";
            case "upcoming":
                return "h-2 w-2 rounded-full bg-amber-400 shadow-[0px_0px_4px_2px_rgba(245,158,11,0.9)]";
            default:
                return "gray";
        }
    }

    // Initialize map once
    useEffect(() => {
        mapboxgl.accessToken = mapboxToken;

        mapRef.current = new mapboxgl.Map({
            container: mapContainerRef.current as HTMLElement,
            style: "mapbox://styles/elghoul/cm3i7q35b001301s69v08h2jr", // Using the new standard style
            center: center,
            zoom: zoom,
            pitch: pitch,
            bearing: bearing,
            antialias: true
        });

        const map = mapRef.current;

        // Set the light preset to dusk when the style is loaded
        map.on("style.load", () => {
            map.setConfigProperty("basemap", "lightPreset", "dusk");
        });

        return () => {
            map.remove();
        };
    }, [center, zoom, pitch, bearing]);

    // Update markers based on data or user position changes
    useEffect(() => {
        const map = mapRef.current;
        if (!map) return;

        // Remove existing markers
        const markers: mapboxgl.Marker[] = [];
        markers.forEach((marker) => marker.remove());
        markers.length = 0;

        // Add markers for buildings
        data.forEach((building) => {
            const el = document.createElement("div");
            el.className = getColorByStatus(building.building_status);

            el.addEventListener("click", () => {
                const accordionItem = document.getElementById(building.building_code);

                setTimeout(() => {
                    if (accordionItem) {
                        accordionItem.scrollIntoView({
                            behavior: "smooth",
                            block: "start",
                        });
                    }
                }, 300);

                handleMarkerClick(building.building_code);
            });

            if (building.coords) {
                const [lat, lng] = building.coords;
                const marker = new mapboxgl.Marker(el)
                    .setLngLat([lng, lat])
                    .addTo(map);
                markers.push(marker);
            }
        });

        // Add user position marker if available
        if (userPos) {
            const e2 = document.createElement("div");
            e2.className =
                "h-3 w-3 border-[1.5px] border-zinc-50 rounded-full bg-blue-400 shadow-[0px_0px_4px_2px_rgba(14,165,233,1)]";

            const [lat, lng] = userPos;
            const userMarker = new mapboxgl.Marker(e2)
                .setLngLat([lng, lat])
                .addTo(map);
            markers.push(userMarker);
        }

        // Cleanup markers on unmount
        return () => {
            markers.forEach((marker) => marker.remove());
        };
    }, [data, userPos, handleMarkerClick]);

    return (
        <div className="h-[60vh] sm:w-full sm:h-full relative bg-red-500/0 rounded-[20px] p-2 sm:p-0">
            <div id="map-container" ref={mapContainerRef} className="opacity-100" />
            <div className="bg-[#18181b]/90 absolute bottom-10 left-2 sm:bottom-8 sm:left-0 flex flex-col gap-2 m-1 py-2.5 p-2 rounded-[16px]">
                <div className="flex items-center gap-0">
                    <div className="h-2 w-2 rounded-full bg-red-400 flex-none"></div>
                    <div className="ml-2 rounded-lg px-2 py-1 text-sm w-full bg-red-700/30 text-red-300/90">
                        unavailable
                    </div>
                </div>
                <div className="flex items-center gap-0">
                    <div className="h-2 w-2 rounded-full bg-amber-400 flex-none"></div>
                    <div className="ml-2 rounded-lg px-2 py-1 text-sm w-full bg-amber-800/30 text-amber-300/90">
                        opening soon
                    </div>
                </div>
                <div className="flex items-center gap-0">
                    <div className="h-2 w-2 rounded-full bg-green-400 flex-none"></div>
                    <div className="ml-2 rounded-lg px-2 py-1 text-sm w-full bg-green-800/30 text-green-300/90">
                        open now
                    </div>
                </div>
            </div>
        </div>
    );
}
