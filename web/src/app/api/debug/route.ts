import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    has_AUTH_SECRET: !!process.env.AUTH_SECRET,
    has_NEXTAUTH_SECRET: !!process.env.NEXTAUTH_SECRET,
    has_AUTH_GOOGLE_ID: !!process.env.AUTH_GOOGLE_ID,
    has_AUTH_GOOGLE_SECRET: !!process.env.AUTH_GOOGLE_SECRET,
    has_GOOGLE_CLIENT_ID: !!process.env.GOOGLE_CLIENT_ID,
    has_GOOGLE_CLIENT_SECRET: !!process.env.GOOGLE_CLIENT_SECRET,
    has_NEXTAUTH_URL: !!process.env.NEXTAUTH_URL,
    NEXTAUTH_URL_value: process.env.NEXTAUTH_URL || "NOT SET",
  });
}
