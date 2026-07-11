import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/api/")) {
    const url = request.nextUrl.clone();
    url.href = url.href.replace(
      `${url.protocol}//${url.host}`,
      process.env.API_TARGET ?? "http://server:8000"
    );
    return NextResponse.rewrite(url);
  }
}

export const config = {
  matcher: "/api/:path*",
};
