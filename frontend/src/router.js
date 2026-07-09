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
import AdminView from "./views/AdminView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/items", name: "items", component: ItemsView },
    { path: "/wanted", name: "wanted", component: WantedView },
    { path: "/favorites", name: "favorites", component: FavoritesView },
    { path: "/notifications", name: "notifications", component: NotificationsView },
    { path: "/publish", name: "publish", component: PublishView },
    { path: "/orders", name: "orders", component: OrdersView },
    { path: "/account", name: "account", component: AccountView },
    { path: "/users", name: "users", component: UserSearchView },
    { path: "/users/:id", name: "user-profile", component: UserProfileView },
    { path: "/chats", name: "chats", component: ChatsView },
    { path: "/contact", name: "contact", component: ContactView },
    { path: "/admin", name: "admin", component: AdminView },
  ],
});

export default router;
