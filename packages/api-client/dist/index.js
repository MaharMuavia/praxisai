import createClient from "openapi-fetch";
export function createPraxisClient(baseUrl) {
    return createClient({
        baseUrl,
        credentials: "include",
    });
}
export async function praxisFetch(baseUrl, path, init) {
    const csrf = typeof document === "undefined"
        ? undefined
        : document.cookie
            .split("; ")
            .find((value) => value.startsWith("praxis_csrf="))
            ?.split("=")[1];
    const response = await fetch(`${baseUrl}${path}`, {
        ...init,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}),
            ...init?.headers,
        },
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const message = typeof payload === "object" && payload !== null && "error" in payload
            ? JSON.stringify(payload)
            : `Request failed (${response.status})`;
        throw new Error(message);
    }
    if (response.status === 204)
        return undefined;
    return (await response.json());
}
