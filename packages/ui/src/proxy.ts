import { NextResponse, type NextRequest } from "next/server"
import { auth } from "@/lib/auth"

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith("/api/auth/")) {
    return NextResponse.next()
  }

  if (pathname.startsWith("/login")) {
    return NextResponse.next()
  }

  if (
    pathname.startsWith("/_next") ||
    pathname.includes(".")
  ) {
    return NextResponse.next()
  }

  const session = await auth()
  if (!session) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set("callbackUrl", request.url)
    return NextResponse.redirect(loginUrl)
  }

  if (pathname.startsWith("/api/")) {
    const url = request.nextUrl.clone()
    url.href = url.href.replace(
      `${url.protocol}//${url.host}`,
      process.env.API_TARGET ?? "http://server:8000"
    )
    return NextResponse.rewrite(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
