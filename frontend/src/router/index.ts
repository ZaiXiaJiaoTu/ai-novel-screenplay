import { createRouter, createWebHistory } from "vue-router";

import HomeView from "@/views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: HomeView },
    { path: "/books", component: () => import("@/views/BooksView.vue") },
    { path: "/scripts", component: () => import("@/views/ScriptsView.vue") },
    {
      path: "/settings/llm-configs",
      component: () => import("@/views/LlmConfigsView.vue")
    },
    {
      path: "/settings/prompt-templates",
      component: () => import("@/views/PromptTemplatesView.vue")
    },
    {
      path: "/settings/llm-logs",
      component: () => import("@/views/LlmLogsView.vue")
    }
  ]
});

export default router;
