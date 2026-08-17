import type { paths } from "./schema";
export type { components, paths } from "./schema";
export declare function createPraxisClient(baseUrl: string): import("openapi-fetch").Client<paths, `${string}/${string}`>;
export declare function praxisFetch<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T>;
