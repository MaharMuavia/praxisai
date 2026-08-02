import { queryOptions } from "@tanstack/react-query";
import type { components } from "@praxisai/api-client";
import { fetchQuery, retryTransientError } from "./shared";

type Notification = components["schemas"]["NotificationView"];
type Preference = components["schemas"]["NotificationPreferenceView"];
export const notificationKeys = {
  all: ["notifications"] as const,
  list: ["notifications", "list"] as const,
  preferences: ["notifications", "preferences"] as const,
};
export const notificationsQuery = () =>
  queryOptions({
    queryKey: notificationKeys.list,
    queryFn: ({ signal }) =>
      fetchQuery<Notification[]>("/notifications", signal),
    retry: retryTransientError,
  });
export const notificationPreferencesQuery = () =>
  queryOptions({
    queryKey: notificationKeys.preferences,
    queryFn: ({ signal }) =>
      fetchQuery<Preference[]>("/notifications/preferences", signal),
    retry: retryTransientError,
  });
