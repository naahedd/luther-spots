import React from "react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface DataFormat {
    building: string;
    building_code: string;
    building_status: string;
    rooms: {
        [key: string]: {
            slots: { StartTime: string; EndTime: string; Status: string }[];
            room_status: string;  // New field for room status
        };
    };
    coords: [number, number];
}

function formatTime(timeString: string) {
    const options = {
        hour: "numeric" as "numeric",
        minute: "numeric" as "numeric",
        hour12: true,
    };
    const time = new Date(`1970-01-01T${timeString}`);
    return new Intl.DateTimeFormat("en-US", options).format(time);
}

// Updated function to display the status label with a semi-transparent background and thinner text
// Updated function to display the status label with more defined border dimensions
function statusLabel(status: string) {
    let labelClass = "";

    if (status === "available") labelClass = "bg-green-800/20 text-green-300 opacity-95";
    else if (status === "upcoming") labelClass = "bg-yellow-800/20 text-yellow-300";
    else labelClass = "bg-red-800/20 text-red-300";

    return (
        <span className={`px-2 py-1 rounded-md text-sm font-medium ${labelClass}`}>
            {status}
        </span>
    );
}


// Room-level status indicator (dot) based on availability
function statusIndicator(status: string) {
    let colorClass = "";

    if (status === "available") colorClass = "bg-green-400";
    else if (status === "upcoming") colorClass = "bg-yellow-400";
    else colorClass = "bg-red-400";

    return <div className={`h-2 w-2 rounded-full ml-2 ${colorClass}`}></div>; // Added "ml-2" for spacing
}

export default function Left({ data, activeBuilding, setActiveBuilding }: {
    data: DataFormat[];
    activeBuilding: string | null;
    setActiveBuilding: (building: string) => void;
}) {
    if (data.length === 0 || !data) {
        return (
            <div className="px-8 my-2">
                <Alert className="mx-auto w-fit text-center">
                    <AlertDescription>Data not available after 10:00 PM</AlertDescription>
                </Alert>
            </div>
        );
    }
    return (
        <div className="px-8">
            <Accordion
                type="single"
                collapsible
                className="w-full"
                value={activeBuilding || ""}
                onValueChange={(val) => setActiveBuilding(val)}
            >
                {data.map((building) => (
                    <AccordionItem
                        id={building.building_code}
                        value={building.building_code}
                        key={building.building_code}
                        className=""
                    >
                        <AccordionTrigger>
                            <div className="flex justify-between w-[95%] text-left text-lg group items-center">
                                <div className="group-hover:underline underline-offset-8 pr-2">
                                    {building.building_code} - {building.building}
                                </div>
                                {statusLabel(building.building_status)}
                            </div>
                        </AccordionTrigger>
                        <AccordionContent className="divide-y divide-dashed divide-zinc-600">
                            {building.rooms &&
                                Object.entries(building.rooms).map(([roomNumber, room]) => (
                                    <div key={roomNumber} className="flex justify-between py-4 text-lg font-[family-name:var(--font-geist-mono)] text-[16px]">
                                        <div className="flex gap-2 items-center h-[fit-content]">
                                            <span>{building.building_code} {roomNumber}</span>
                                            {statusIndicator(room.room_status)}
                                        </div>
                                        <ul className="text-right">
                                            {room.slots.map((slot, index) => (
                                                <li key={index}>
                                                    {formatTime(slot.StartTime)} - {formatTime(slot.EndTime)}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                        </AccordionContent>
                    </AccordionItem>
                ))}
            </Accordion>
        </div>
    );
}
