import { createRouter, createWebHistory } from "vue-router";
import HomeView from "./views/HomeView.vue";
import ItemsView from "./views/ItemsView.vue";
import PublishView from "./views/PublishView.vue";
import AccountView from "./views/AccountView.vue";
import FavoritesView from "./views/FavoritesView.vue";
import NotificationsView from "./views/NotificationsView.vue";
import OrdersView from "./views/OrdersView.vue";
import WantedView from "./views/WantedView.vue";
import UserSearchView from "./views/UserSearchView.vue";
import UserProfileView from "./views/UserProfileView.vue";
import ChatsView from "./views/ChatsView.vue";
import ContactView from "./views/ContactView.vue";
import BrowsingHistoryView from "./views/BrowsingHistoryView.vue";
import AdminView from "./views/AdminView.vue";
import AdminItemsView from "./views/AdminItemsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/items", name: "items", component: ItemsView },
    { path: "/wanted", name: "wanted", component: WantedView },
    { path: "/favorites", name: "favorites", component: FavoritesView, meta: { requiresAuth: true } },
    { path: "/notifications", name: "notifications", component: NotificationsView, meta: { requiresAuth: true } },
    { path: "/publish", name: "publish", component: PublishView, meta: { requiresAuth: true } },
    { path: "/orders", name: "orders", component: OrdersView, meta: { requiresAuth: true } },
    { path: "/account", name: "account", component: AccountView },
    { path: "/users", name: "users", component: UserSearchView },
    { path: "/users/:id", name: "user-profile", component: UserProfileView },
    { path: "/chats", name: "chats", component: ChatsView, meta: { requiresAuth: true } },
    { path: "/contact", name: "contact", component: ContactView },
    { path: "/history", name: "history", component: BrowsingHistoryView, meta: { requiresAuth: true } },
    { path: "/admin", name: "admin", component: AdminView, meta: { requiresAdmin: true } },
    { path: "/admin/items", name: "admin-items", component: AdminItemsView, meta: { requiresAdmin: true } },
  ],
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("campus-market-token") || "";
  const principal = JSON.parse(localStorage.getItem("campus-market-principal") || "null");

  if (to.meta.requiresAuth && !token) {
    return next("/account");
  }
  if (to.meta.requiresAdmin && principal?.kind !== "admin") {
    return next("/");
  }
  next();
});

export default router;
