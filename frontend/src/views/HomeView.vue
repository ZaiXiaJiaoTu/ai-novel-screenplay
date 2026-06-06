<template>
  <section class="home-page">
    <div class="page-header">
      <h1 class="page-title">工作台</h1>
      <p class="page-subtitle">
        从小说上传开始，先维护章节切分，再进入剧本改编流程；模型配置和调用日志用于排查生成质量。
      </p>
    </div>
    <div class="home-actions">
      <el-button type="primary" :icon="Collection" @click="go('/books')">进入小说书架</el-button>
      <el-button type="primary" plain :icon="Document" @click="go('/scripts')">进入剧本生成</el-button>
      <el-button :icon="Setting" @click="go('/settings/llm-configs')">模型配置</el-button>
    </div>
    <el-row :gutter="16">
      <el-col v-for="item in cards" :key="item.title" :xs="24" :sm="8">
        <el-card class="workflow-card" shadow="never">
          <template #header>{{ item.title }}</template>
          <p class="page-subtitle">{{ item.description }}</p>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { Collection, Document, Setting } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";

const router = useRouter();

const cards = [
  { title: "1. 上传小说", description: "在小说书架上传 txt 或粘贴正文，系统按章节切分，后续可手动增删改章节。" },
  { title: "2. 改编剧本", description: "选择小说创建改编项目，按批次拆分剧情事件，维护人物档案并生成分集剧本。" },
  { title: "3. 导出与排查", description: "在剧本模块导出分集或全集；生成异常时到模型配置和调用日志检查提示词与响应。" }
];

function go(path: string) {
  void router.push(path);
}
</script>
