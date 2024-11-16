// /app/api/open-classrooms/route.ts
import { NextResponse } from "next/server";
const backendUrl = 'https://luther-spots.onrender.com';

export async function POST(req: Request) {
    try {
        const { lat, lng } = await req.json();

        // Make a request to the local backend
        const response = await fetch(`${backendUrl}/api/open-classrooms`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ lat, lng }),
        });

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch data" },
                { status: 500 }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error in POST route:", error);
        return NextResponse.json(
            { error: "Failed to process request" },
            { status: 500 }
        );
    }
}

export async function GET() {
    try {
        const response = await fetch(`${backendUrl}/api/open-classrooms`, {
            method: "GET",
            cache: "no-cache",
        });

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch data" },
                { status: 500 }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error in GET route:", error);
        return NextResponse.json(
            { error: "Failed to process request" },
            { status: 500 }
        );
    }
}
