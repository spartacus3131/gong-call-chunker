import { NextRequest, NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import { SignJWT } from "jose";

const BACKEND =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SECRET = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET || "";

async function proxyRequest(req: NextRequest) {
  // 1. Decode session cookie → next-auth token
  const token = await getToken({ req, secret: SECRET });

  // 2. Build Authorization header if we have a session
  const headers: Record<string, string> = {};
  if (token?.sub && token?.email) {
    const jwt = await new SignJWT({
      sub: token.sub as string,
      email: token.email as string,
      name: (token.name as string) ?? "",
      picture: (token.picture as string) ?? "",
    })
      .setProtectedHeader({ alg: "HS256" })
      .setIssuedAt()
      .setExpirationTime("5m")
      .sign(new TextEncoder().encode(SECRET));

    headers["Authorization"] = `Bearer ${jwt}`;
  }

  // 3. Build backend URL
  const url = new URL(req.url);
  const backendUrl = `${BACKEND}${url.pathname}${url.search}`;

  // 4. Forward content-type and body
  const contentType = req.headers.get("content-type");
  if (contentType) {
    headers["content-type"] = contentType;
  }

  const body =
    req.method !== "GET" && req.method !== "HEAD"
      ? await req.arrayBuffer()
      : undefined;

  // 5. Fetch from backend
  const resp = await fetch(backendUrl, {
    method: req.method,
    headers,
    body,
  });

  // 6. Return backend response
  const respBody = await resp.arrayBuffer();
  const respHeaders = new Headers();
  resp.headers.forEach((value, key) => {
    // Skip hop-by-hop headers
    if (!["transfer-encoding", "connection"].includes(key.toLowerCase())) {
      respHeaders.set(key, value);
    }
  });

  return new NextResponse(respBody, {
    status: resp.status,
    headers: respHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
