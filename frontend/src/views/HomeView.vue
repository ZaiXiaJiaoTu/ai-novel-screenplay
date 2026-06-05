<template>
  <section>
    <div class="page-header">
      <h1 class="page-title">工作台</h1>
      <p class="page-subtitle">按小说导入、预处理、剧本生成、剧本书架的闭环推进。</p>
    </div>
    <el-row :gutter="16">
      <el-col v-for="item in cards" :key="item.title" :xs="24" :sm="8">
        <el-card shadow="never">
          <template #header>{{ item.title }}</template>
          <p class="page-subtitle">{{ item.description }}</p>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
const cards = [
  { title: "待选书架", description: "导入小说文本，查看作品和章节，触发章节摘要预处理。" },
  { title: "剧本书架", description: "查看、编辑和下载生成后的剧本片段。" },
  { title: "系统配置", description: "管理大模型 API、提示词模板和调用日志。" }
];
</script>
