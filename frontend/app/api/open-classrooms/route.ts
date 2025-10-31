// /app/api/open-classrooms/route.ts
import { NextResponse } from "next/server";

// Use environment variable for backend URL
const backendUrl = 'https://luther-spots-1.onrender.com';

// Helper to ensure consistent URL formatting
const getBackendUrl = (path: string) => {
    const baseUrl = backendUrl.endsWith('/') ? backendUrl.slice(0, -1) : backendUrl;
    return `${baseUrl}${path}`;
};

export async function POST(req: Request) {
    try {
        const { lat, lng } = await req.json();

        const response = await fetch(getBackendUrl('/api/open-classrooms'), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ lat, lng }),
        });

        if (!response.ok) {
            console.error(`Backend responded with status: ${response.status}`);
            return NextResponse.json(
                { error: `Failed to fetch data: ${response.statusText}` },
                { status: response.status }
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
        const response = await fetch(getBackendUrl('/api/open-classrooms'), {
            method: "GET",
            headers: {
                "Accept": "application/json",
            },
            cache: "no-cache",
        });

        if (!response.ok) {
            console.error(`Backend responded with status: ${response.status}`);
            return NextResponse.json(
                { error: `Failed to fetch data: ${response.statusText}` },
                { status: response.status }
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