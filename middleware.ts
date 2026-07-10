import { type NextRequest, NextResponse } from "next/server";

const PROTECTED_ROUTES = [
  "/dashboard",
  "/upload",
  "/analyze",
  "/claims",
  "/investigations",
  "/reports",
  "/analytics",
  "/settings",
];

const PUBLIC_ROUTES = ["/", "/login", "/signup", "/auth/callback"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtectedRoute = PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + "/"),
  );

  const isPublicRoute = PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + "/"),
  );

  if (!isProtectedRoute && !isPublicRoute) {
    return NextResponse.next();
  }

  if (isPublicRoute && pathname !== "/") {
    const sessionCookie = request.cookies.get("insforge-auth");
    if (sessionCookie) {
      try {
        const session = JSON.parse(sessionCookie.value);
        if (session?.accessToken) {
          return NextResponse.redirect(new URL("/dashboard", request.url));
        }
      } catch {
        // Invalid session cookie, continue to public page
      }
    }
  }

  if (isProtectedRoute) {
    const sessionCookie = request.cookies.get("insforge-auth");

    if (!sessionCookie) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    try {
      const session = JSON.parse(sessionCookie.value);
      if (!session?.accessToken) {
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("redirect", pathname);
        return NextResponse.redirect(loginUrl);
      }
    } catch {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/upload/:path*",
    "/analyze/:path*",
    "/claims/:path*",
    "/investigations/:path*",
    "/reports/:path*",
    "/analytics/:path*",
    "/settings/:path*",
    "/login",
    "/signup",
    "/auth/callback",
  ],
};
