import { createRouter, createWebHistory } from "vue-router";

import HomeView from "@/views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: HomeView },
    { path: "/books", component: () => import("@/views/PlaceholderView.vue") },
    { path: "/scripts", component: () => import("@/views/PlaceholderView.vue") },
    {
      path: "/settings/llm-configs",
      component: () => import("@/views/PlaceholderView.vue")
    }
  ]
});

export default router;
