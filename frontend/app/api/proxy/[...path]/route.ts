import { NextRequest, NextResponse } from 'next/server';

// Use Docker internal hostname for server-side requests
const API_BASE = 'http://backend:8000';

// Helper to forward headers while preserving critical ones
function forwardHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'host': new URL(API_BASE).host,
  };

  // Forward important headers
  const headersToForward = [
    'authorization',
    'content-type',
    'accept',
    'user-agent',
  ];

  headersToForward.forEach((headerName) => {
    const value = request.headers.get(headerName);
    if (value) {
      headers[headerName] = value;
    }
  });

  return headers;
}

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const pathStr = params.path.join('/');
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${API_BASE}/${pathStr}${searchParams ? '?' + searchParams : ''}`;

  try {
    const response = await fetch(url, {
      headers: forwardHeaders(request),
    });

    return new NextResponse(response.body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ error: 'Proxy error' }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const pathStr = params.path.join('/');
  const url = `${API_BASE}/${pathStr}`;

  try {
    const body = await request.text();
    const response = await fetch(url, {
      method: 'POST',
      headers: forwardHeaders(request),
      body: body || undefined,
    });

    return new NextResponse(response.body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ error: 'Proxy error' }, { status: 500 });
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const pathStr = params.path.join('/');
  const url = `${API_BASE}/${pathStr}`;

  try {
    const body = await request.text();
    const response = await fetch(url, {
      method: 'PATCH',
      headers: forwardHeaders(request),
      body: body || undefined,
    });

    return new NextResponse(response.body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ error: 'Proxy error' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const pathStr = params.path.join('/');
  const url = `${API_BASE}/${pathStr}`;

  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: forwardHeaders(request),
    });

    return new NextResponse(response.body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ error: 'Proxy error' }, { status: 500 });
  }
}
