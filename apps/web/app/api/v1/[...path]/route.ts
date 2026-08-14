import { GoogleAuth } from "google-auth-library";
import { NextRequest, NextResponse } from "next/server";

import {
  buildApiProxyTarget,
  buildForwardHeaders,
  resolveApiProxyTimeoutMs,
  responseHeaders,
} from "@/lib/api-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const AUTHENTICATED_ENVIRONMENTS = new Set(["staging", "production"]);

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

type NodeStreamingRequestInit = RequestInit & {
  duplex: "half";
};

function correlationId(request: NextRequest): string {
  const supplied = request.headers.get("x-correlation-id")?.trim();
  return supplied && supplied.length <= 128 ? supplied : crypto.randomUUID();
}

async function apiRequestHeaders(
  apiBaseUrl: string,
  headers: Headers,
): Promise<Headers> {
  const appEnvironment = process.env.APP_ENV ?? "local";
  if (!AUTHENTICATED_ENVIRONMENTS.has(appEnvironment)) {
    return headers;
  }

  const auth = new GoogleAuth();
  const client = await auth.getIdTokenClient(new URL(apiBaseUrl).origin);
  const authorization = await client.getRequestHeaders();
  const authorizationValue = authorization.get("authorization");
  if (!authorizationValue) {
    throw new Error("Google service authentication did not return an ID token");
  }
  headers.set("authorization", authorizationValue);
  return headers;
}

function upstreamRequestInit(
  request: NextRequest,
  headers: Headers,
  signal: AbortSignal,
): RequestInit {
  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "error",
    signal,
    cache: "no-store",
  };
  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    const streamingInit: NodeStreamingRequestInit = {
      ...init,
      body: request.body,
      duplex: "half",
    };
    return streamingInit;
  }
  return init;
}

async function proxyRequest(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const apiBaseUrl = process.env.API_BASE_URL?.trim();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "API proxy is not configured" },
      { status: 503 },
    );
  }

  const { path } = await context.params;
  const appEnvironment = process.env.APP_ENV ?? "local";
  let target: URL;
  let timeoutMs: number;
  try {
    target = buildApiProxyTarget(
      apiBaseUrl,
      path,
      request.nextUrl.search,
      appEnvironment,
    );
    timeoutMs = resolveApiProxyTimeoutMs(process.env.API_PROXY_TIMEOUT_MS);
  } catch (error) {
    console.error("Invalid API proxy configuration", error);
    return NextResponse.json(
      { detail: "API proxy configuration is invalid" },
      { status: 500 },
    );
  }

  const headers = buildForwardHeaders(request.headers, correlationId(request));
  const timeoutSignal = AbortSignal.timeout(timeoutMs);
  try {
    await apiRequestHeaders(apiBaseUrl, headers);
    const upstreamSignal = AbortSignal.any([request.signal, timeoutSignal]);
    const response = await fetch(
      target,
      upstreamRequestInit(request, headers, upstreamSignal),
    );

    return new NextResponse(response.body, {
      status: response.status,
      headers: responseHeaders(response.headers),
    });
  } catch (error) {
    if (request.signal.aborted) {
      console.info("API proxy request cancelled by client");
      return new NextResponse(null, { status: 499 });
    }
    if (timeoutSignal.aborted) {
      console.error("API proxy request timed out", { timeoutMs });
      return NextResponse.json(
        { detail: "API service timed out" },
        { status: 504 },
      );
    }
    const message =
      error instanceof Error ? error.message : "unknown proxy error";
    console.error("API proxy request failed", { message });
    return NextResponse.json(
      { detail: "API service unavailable" },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const HEAD = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
