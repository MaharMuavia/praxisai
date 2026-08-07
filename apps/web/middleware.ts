import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = [
  "/",
  "/login",
  "/verify",
  "/about",
  "/students",
  "/companies",
  "/pricing",
  "/trust",
  "/impact",
  "/contact",
  "/business-model",
  "/evidence",
  "/internships",
  "/judge",
  "/api",
] as const;

const WORKSPACE_PATHS = [
  "/admin",
  "/client",
  "/lead",
  "/ops",
  "/student",
  "/university",
] as const;

function matchesPath(pathname: string, path: string): boolean {
  return pathname === path || pathname.startsWith(`${path}/`);
}

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some((path) => matchesPath(pathname, path));
}

function isWorkspacePath(pathname: string): boolean {
  return WORKSPACE_PATHS.some((path) => matchesPath(pathname, path));
}

function correlationId(request: NextRequest): string {
  const supplied = request.headers.get("x-correlation-id")?.trim();
  return supplied || crypto.randomUUID();
}

function withCorrelationId(response: NextResponse, id: string): NextResponse {
  response.headers.set("X-Correlation-ID", id);
  return response;
}

export function middleware(request: NextRequest): NextResponse {
  const id = correlationId(request);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("X-Correlation-ID", id);

  if (
    isWorkspacePath(request.nextUrl.pathname) &&
    !isPublicPath(request.nextUrl.pathname)
  ) {
    const session = request.cookies.get("praxis_session")?.value;
    if (!session) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set(
        "redirect",
        `${request.nextUrl.pathname}${request.nextUrl.search}`,
      );
      return withCorrelationId(NextResponse.redirect(loginUrl), id);
    }
  }

  return withCorrelationId(
    NextResponse.next({ request: { headers: requestHeaders } }),
    id,
  );
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
