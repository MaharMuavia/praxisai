const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

const PRODUCTION_ENVIRONMENTS = new Set(["staging", "production"]);

export function buildApiProxyTarget(
  configuredApiBase: string,
  pathSegments: readonly string[],
  search: string,
  appEnvironment: string,
): URL {
  const base = new URL(configuredApiBase);
  if (!base.protocol.startsWith("http")) {
    throw new Error("API_BASE_URL must use HTTP or HTTPS");
  }
  if (base.username || base.password || base.hash) {
    throw new Error("API_BASE_URL must not contain credentials or fragments");
  }
  if (
    PRODUCTION_ENVIRONMENTS.has(appEnvironment) &&
    base.protocol !== "https:"
  ) {
    throw new Error("Hosted API_BASE_URL must use HTTPS");
  }

  const basePath = base.pathname.replace(/\/$/, "");
  const apiPath = basePath.endsWith("/api/v1")
    ? basePath
    : `${basePath}/api/v1`;
  const encodedPath = pathSegments
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  base.pathname = `${apiPath}/${encodedPath}`;
  base.search = search;
  return base;
}

export function buildForwardHeaders(
  requestHeaders: Headers,
  correlationId: string,
): Headers {
  const headers = new Headers();
  requestHeaders.forEach((value, name) => {
    if (!HOP_BY_HOP_HEADERS.has(name.toLowerCase())) {
      headers.set(name, value);
    }
  });
  headers.set("x-correlation-id", correlationId);
  return headers;
}

export function responseHeaders(source: Headers): Headers {
  const headers = new Headers();
  source.forEach((value, name) => {
    if (!HOP_BY_HOP_HEADERS.has(name.toLowerCase())) {
      headers.set(name, value);
    }
  });
  return headers;
}
