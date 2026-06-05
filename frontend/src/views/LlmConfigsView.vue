<template>
  <section class="settings-page">
    <div class="page-header settings-header">
      <div>
        <h1 class="page-title">模型配置</h1>
        <p class="page-subtitle">管理大模型网关、模型名称和调用参数，供摘要与剧本生成链路使用。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增配置</el-button>
    </div>

    <section class="settings-panel">
      <el-table v-loading="loading" :data="configs" empty-text="暂无模型配置">
        <el-table-column prop="provider" label="供应商" width="120" />
        <el-table-column prop="model_name" label="模型" min-width="180" />
        <el-table-column prop="base_url" label="Base URL" min-width="260" show-overflow-tooltip />
        <el-table-column prop="api_key_masked" label="API Key" width="150" />
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">默认</el-tag>
            <el-tag v-else-if="row.enabled">启用</el-tag>
            <el-tag v-else type="info">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="参数" width="170">
          <template #default="{ row }">
            <span>T {{ row.temperature ?? "-" }} / TopP {{ row.top_p ?? "-" }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="330" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" :icon="Connection" :loading="testingId === row.config_id" @click="runTest(row)">
              测试
            </el-button>
            <el-button size="small" :disabled="row.is_default" @click="markDefault(row)">设默认</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="removeConfig(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingConfig ? '编辑模型配置' : '新增模型配置'" width="680px">
      <el-form label-position="top">
        <div class="settings-form-grid">
          <el-form-item label="供应商">
            <el-input v-model="form.provider" placeholder="deepseek" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="form.model_name" placeholder="deepseek-chat" />
          </el-form-item>
        </div>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
        </el-form-item>
        <el-form-item :label="editingConfig ? 'API Key（留空则不修改）' : 'API Key'">
          <el-input v-model="form.api_key" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <div class="settings-form-grid">
          <el-form-item label="Temperature">
            <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" />
          </el-form-item>
          <el-form-item label="Top P">
            <el-input-number v-model="form.top_p" :min="0" :max="1" :step="0.05" />
          </el-form-item>
          <el-form-item label="Max Tokens">
            <el-input-number v-model="form.max_tokens" :min="1" :step="100" />
          </el-form-item>
        </div>
        <div class="settings-form-grid">
          <el-form-item label="超时秒数">
            <el-input-number v-model="form.timeout_seconds" :min="1" />
          </el-form-item>
          <el-form-item label="重试次数">
            <el-input-number v-model="form.retry_count" :min="0" />
          </el-form-item>
        </div>
        <el-form-item label="任务范围">
          <el-select v-model="form.task_scope" multiple clearable placeholder="为空表示所有任务">
            <el-option v-for="task in taskOptions" :key="task" :label="task" :value="task" />
          </el-select>
        </el-form-item>
        <div class="settings-switches">
          <el-checkbox v-model="form.enabled">启用配置</el-checkbox>
          <el-checkbox v-model="form.is_default">设为默认</el-checkbox>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { Connection, Delete, Edit, Plus } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, reactive, ref } from "vue";

import {
  type LlmConfigDetail,
  type LlmConfigPayload,
  createLlmConfig,
  deleteLlmConfig,
  fetchLlmConfigs,
  setDefaultLlmConfig,
  testLlmConfig,
  updateLlmConfig
} from "@/api/client";

const taskOptions = [
  "story_profile_generation",
  "chapter_summary_generation",
  "style_strategy_generation",
  "scene_plan_generation",
  "script_yaml_generation",
  "yaml_repair"
];

const configs = ref<LlmConfigDetail[]>([]);
const loading = ref(false);
const saving = ref(false);
const testingId = ref<number | null>(null);
const dialogVisible = ref(false);
const editingConfig = ref<LlmConfigDetail | null>(null);
const form = reactive<LlmConfigPayload & { api_key: string }>({
  provider: "deepseek",
  base_url: "https://api.deepseek.com/v1",
  api_key: "",
  model_name: "deepseek-chat",
  temperature: 0.7,
  top_p: 0.9,
  max_tokens: 4096,
  timeout_seconds: 60,
  retry_count: 2,
  task_scope: null,
  enabled: true,
  is_default: true
});

function resetForm() {
  Object.assign(form, {
    provider: "deepseek",
    base_url: "https://api.deepseek.com/v1",
    api_key: "",
    model_name: "deepseek-chat",
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 4096,
    timeout_seconds: 60,
    retry_count: 2,
    task_scope: null,
    enabled: true,
    is_default: configs.value.length === 0
  });
}

async function loadConfigs() {
  loading.value = true;
  try {
    configs.value = await fetchLlmConfigs();
  } finally {
    loading.value = false;
  }
}

function openCreateDialog() {
  editingConfig.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(config: LlmConfigDetail) {
  editingConfig.value = config;
  Object.assign(form, {
    provider: config.provider,
    base_url: config.base_url,
    api_key: "",
    model_name: config.model_name,
    temperature: config.temperature === null ? null : Number(config.temperature),
    top_p: config.top_p === null ? null : Number(config.top_p),
    max_tokens: config.max_tokens,
    timeout_seconds: config.timeout_seconds,
    retry_count: config.retry_count,
    task_scope: config.task_scope,
    enabled: config.enabled,
    is_default: config.is_default
  });
  dialogVisible.value = true;
}

function buildPayload() {
  const payload: Partial<LlmConfigPayload> = {
    provider: form.provider.trim(),
    base_url: form.base_url.trim(),
    model_name: form.model_name.trim(),
    temperature: form.temperature,
    top_p: form.top_p,
    max_tokens: form.max_tokens,
    timeout_seconds: form.timeout_seconds,
    retry_count: form.retry_count,
    task_scope: form.task_scope?.length ? form.task_scope : null,
    enabled: form.enabled,
    is_default: form.is_default
  };
  if (form.api_key.trim()) {
    payload.api_key = form.api_key.trim();
  }
  return payload;
}

async function saveConfig() {
  if (!form.provider.trim() || !form.base_url.trim() || !form.model_name.trim()) {
    ElMessage.warning("请填写供应商、Base URL 和模型名称");
    return;
  }
  if (!editingConfig.value && !form.api_key.trim()) {
    ElMessage.warning("新增配置必须填写 API Key");
    return;
  }
  saving.value = true;
  try {
    if (editingConfig.value) {
      await updateLlmConfig(editingConfig.value.config_id, buildPayload());
    } else {
      await createLlmConfig(buildPayload() as LlmConfigPayload & { api_key: string });
    }
    ElMessage.success("保存成功");
    dialogVisible.value = false;
    await loadConfigs();
  } finally {
    saving.value = false;
  }
}

async function markDefault(config: LlmConfigDetail) {
  await setDefaultLlmConfig(config.config_id);
  ElMessage.success("已设为默认配置");
  await loadConfigs();
}

async function runTest(config: LlmConfigDetail) {
  testingId.value = config.config_id;
  try {
    const result = await testLlmConfig(config.config_id);
    ElMessage.success(`测试通过，延迟 ${result.latency_ms} ms`);
  } finally {
    testingId.value = null;
  }
}

async function removeConfig(config: LlmConfigDetail) {
  await ElMessageBox.confirm(`确定删除 ${config.provider} / ${config.model_name}？`, "删除配置", {
    type: "warning"
  });
  await deleteLlmConfig(config.config_id);
  ElMessage.success("已删除配置");
  await loadConfigs();
}

onMounted(loadConfigs);
</script>
