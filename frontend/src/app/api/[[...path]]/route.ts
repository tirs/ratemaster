import { NextRequest, NextResponse } from "next/server";

const BACKEND =
  process.env.API_BACKEND ||
  process.env.NEXT_PUBLIC_API_BACKEND ||
  "http://localhost:30080";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path = [] } = await params;
  return proxy(request, path, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path = [] } = await params;
  return proxy(request, path, "POST");
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path = [] } = await params;
  return proxy(request, path, "PATCH");
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path = [] } = await params;
  return proxy(request, path, "PUT");
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path = [] } = await params;
  return proxy(request, path, "DELETE");
}

export async function OPTIONS(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path = [] } = await params;
  return proxy(request, path, "OPTIONS");
}

async function proxy(
  request: NextRequest,
  path: string[],
  method: string
) {
  const pathStr = path.join("/");
  const url = new URL(request.url);
  const backendUrl = `${BACKEND}/api/${pathStr}${url.search}`;

  const headers = new Headers();
  request.headers.forEach((v, k) => {
    const lower = k.toLowerCase();
    if (lower !== "host" && lower !== "content-length") headers.set(k, v);
  });

  let body: BodyInit | undefined;
  if (method !== "GET") {
    body = await request.arrayBuffer();
    if (body.byteLength === 0) body = undefined;
  }

  try {
    const res = await fetch(backendUrl, {
      method,
      headers,
      body: body || undefined,
    });
    const data = await res.text();
    if (res.status >= 400) {
      console.error(`API proxy ${method} ${backendUrl} -> ${res.status}`, data.slice(0, 500));
    }
    return new NextResponse(data, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("Content-Type") || "application/json",
      },
    });
  } catch (err) {
    console.error("API proxy error:", err);
    return NextResponse.json(
      { success: false, error: "Backend unavailable. Is it running on " + BACKEND + "?" },
      { status: 502 }
    );
  }
}
