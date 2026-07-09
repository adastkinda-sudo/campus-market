import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api/client.js";
import { useSessionStore } from "./session.js";

export const useCommonStore = defineStore("common", () => {
  const categories = ref([]);
  const locations = ref([]);
  const announcements = ref([]);
  const dashboard = ref(null);

  async function loadCommon() {
    const [cats, locs, anns, dash] = await Promise.all([
      api("/api/categories"),
      api("/api/locations"),
      api("/api/announcements"),
      api("/api/dashboard"),
    ]);
    categories.value = cats.categories || [];
    locations.value = locs.locations || [];
    announcements.value = anns.announcements || [];
    dashboard.value = dash;

    const session = useSessionStore();
    if (session.isUser) {
      try {
        const notifications = await api("/api/notifications");
        session.unreadCount = notifications.unreadCount || 0;
      } catch {
        session.unreadCount = 0;
      }
    } else {
      session.unreadCount = 0;
    }
  }

  return { categories, locations, announcements, dashboard, loadCommon };
});
