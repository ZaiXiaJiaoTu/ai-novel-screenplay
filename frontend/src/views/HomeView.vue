<template>
  <section>
    <div class="page-header">
      <h1 class="page-title">工作台</h1>
      <p class="page-subtitle">按小说上传、预处理、剧本生成、剧本书架的闭环推进。</p>
    </div>
    <el-row :gutter="16">
      <el-col v-for="item in cards" :key="item.title" :span="8">
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
  { title: "待选书架", description: "管理上传后完成预处理的小说作品。" },
  { title: "剧本书架", description: "查看、编辑和下载生成后的剧本片段。" },
  { title: "系统配置", description: "管理大模型 API、提示词模板和调用日志。" }
];
</script>
