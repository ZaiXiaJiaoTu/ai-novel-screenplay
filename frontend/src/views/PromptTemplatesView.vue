<template>
  <section class="settings-page">
    <div class="page-header settings-header">
      <div>
        <h1 class="page-title">提示词模板</h1>
        <p class="page-subtitle">管理各生成任务使用的 system prompt、用户模板、变量和历史版本。</p>
      </div>
      <div class="settings-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadTemplates">刷新</el-button>
        <el-button :icon="MagicStick" :loading="seeding" @click="seedDefaults">初始化默认模板</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增模板</el-button>
      </div>
    </div>

    <section class="settings-panel">
      <div class="template-filters">
        <el-input v-model="filters.keyword" clearable placeholder="按模板名称搜索" @change="loadTemplates" />
        <el-select v-model="filters.task_type" clearable placeholder="任务类型" @change="loadTemplates">
          <el-option v-for="task in taskOptions" :key="task" :label="task" :value="task" />
        </el-select>
        <el-select v-model="filters.enabled" clearable placeholder="启用状态" @change="loadTemplates">
          <el-option label="启用" :value="true" />
          <el-option label="停用" :value="false" />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="templates" empty-text="暂无提示词模板">
        <el-table-column prop="template_name" label="模板名称" min-width="190" />
        <el-table-column prop="task_type" label="任务类型" min-width="210" show-overflow-tooltip />
        <el-table-column prop="output_format" label="格式" width="90" />
        <el-table-column label="版本" width="90">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column label="变量" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.variables?.join(", ") || "-" }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? "启用" : "停用" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" :icon="Clock" @click="openVersions(row)">版本</el-button>
            <el-button size="small" @click="toggleTemplate(row)">
              {{ row.enabled ? "停用" : "启用" }}
            </el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="removeTemplate(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingTemplate ? '编辑提示词模板' : '新增提示词模板'" width="860px">
      <el-form label-position="top">
        <div class="settings-form-grid">
          <el-form-item label="模板名称">
            <el-input v-model="form.template_name" />
          </el-form-item>
          <el-form-item label="任务类型">
            <el-input v-model="form.task_type" />
          </el-form-item>
          <el-form-item label="输出格式">
            <el-select v-model="form.output_format">
              <el-option label="json" value="json" />
              <el-option label="yaml" value="yaml" />
              <el-option label="text" value="text" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="变量">
          <el-input v-model="variablesText" placeholder="用英文逗号分隔，例如 book_title, chapters" />
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="User Prompt Template">
          <el-input v-model="form.user_prompt_template" type="textarea" :rows="9" />
        </el-form-item>
        <el-checkbox v-model="form.enabled">启用模板</el-checkbox>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="versionsVisible" title="模板版本" size="620px">
      <el-table v-loading="loadingVersions" :data="versions" empty-text="暂无版本">
        <el-table-column label="版本" width="80">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column prop="output_format" label="格式" width="90" />
        <el-table-column label="变量" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.variables?.join(", ") || "-" }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="rollbackVersion(row)">回滚</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-collapse class="version-preview">
        <el-collapse-item v-for="item in versions" :key="item.version_id" :title="`v${item.version} 预览`">
          <pre>{{ item.system_prompt }}</pre>
          <pre>{{ item.user_prompt_template }}</pre>
        </el-collapse-item>
      </el-collapse>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { Clock, Delete, Edit, MagicStick, Plus, Refresh } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onMounted, reactive, ref } from "vue";

import {
  type PromptTemplateDetail,
  type PromptTemplatePayload,
  type PromptTemplateVersionDetail,
  createPromptTemplate,
  deletePromptTemplate,
  fetchPromptTemplateVersions,
  fetchPromptTemplates,
  rollbackPromptTemplate,
  seedDefaultPromptTemplates,
  updatePromptTemplate
} from "@/api/client";

const taskOptions = [
  "plot_event_split_generation",
  "script_episode_generation"
];

const templates = ref<PromptTemplateDetail[]>([]);
const versions = ref<PromptTemplateVersionDetail[]>([]);
const loading = ref(false);
const saving = ref(false);
const seeding = ref(false);
const loadingVersions = ref(false);
const dialogVisible = ref(false);
const versionsVisible = ref(false);
const editingTemplate = ref<PromptTemplateDetail | null>(null);
const versionTemplate = ref<PromptTemplateDetail | null>(null);
const variablesText = ref("");
const filters = reactive<{
  keyword: string;
  task_type: string;
  enabled: boolean | undefined;
}>({
  keyword: "",
  task_type: "",
  enabled: undefined
});
const form = reactive<PromptTemplatePayload>({
  template_name: "",
  task_type: "",
  system_prompt: "",
  user_prompt_template: "",
  output_format: "json",
  variables: null,
  enabled: true
});

function parseVariables() {
  const values = variablesText.value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return values.length ? values : null;
}

function resetForm() {
  Object.assign(form, {
    template_name: "",
    task_type: "",
    system_prompt: "",
    user_prompt_template: "",
    output_format: "json",
    variables: null,
    enabled: true
  });
  variablesText.value = "";
}

async function loadTemplates() {
  loading.value = true;
  try {
    templates.value = await fetchPromptTemplates({
      keyword: filters.keyword || undefined,
      task_type: filters.task_type || undefined,
      enabled: filters.enabled
    });
  } catch {
    templates.value = [];
    ElMessage.error("提示词模板加载失败，请检查后端服务和数据库连接");
  } finally {
    loading.value = false;
  }
}

async function seedDefaults() {
  seeding.value = true;
  try {
    await seedDefaultPromptTemplates();
    ElMessage.success("默认模板已初始化");
    await loadTemplates();
  } catch {
    ElMessage.error("默认模板初始化失败");
  } finally {
    seeding.value = false;
  }
}

function openCreateDialog() {
  editingTemplate.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(template: PromptTemplateDetail) {
  editingTemplate.value = template;
  Object.assign(form, {
    template_name: template.template_name,
    task_type: template.task_type,
    system_prompt: template.system_prompt,
    user_prompt_template: template.user_prompt_template,
    output_format: template.output_format,
    variables: template.variables,
    enabled: template.enabled
  });
  variablesText.value = template.variables?.join(", ") || "";
  dialogVisible.value = true;
}

async function saveTemplate() {
  if (
    !form.template_name.trim() ||
    !form.task_type.trim() ||
    !form.system_prompt.trim() ||
    !form.user_prompt_template.trim()
  ) {
    ElMessage.warning("请填写模板名称、任务类型和提示词内容");
    return;
  }
  saving.value = true;
  try {
    const payload = { ...form, variables: parseVariables() };
    if (editingTemplate.value) {
      await updatePromptTemplate(editingTemplate.value.template_id, payload);
    } else {
      await createPromptTemplate(payload);
    }
    ElMessage.success("保存成功");
    dialogVisible.value = false;
    await loadTemplates();
  } catch {
    ElMessage.error("模板保存失败");
  } finally {
    saving.value = false;
  }
}

async function toggleTemplate(template: PromptTemplateDetail) {
  try {
    await updatePromptTemplate(template.template_id, { enabled: !template.enabled });
    ElMessage.success(template.enabled ? "已停用模板" : "已启用模板");
    await loadTemplates();
  } catch {
    ElMessage.error("模板状态更新失败");
  }
}

async function removeTemplate(template: PromptTemplateDetail) {
  try {
    await ElMessageBox.confirm(`确定删除 ${template.template_name}？`, "删除模板", {
      type: "warning"
    });
    await deletePromptTemplate(template.template_id);
    ElMessage.success("已删除模板");
    await loadTemplates();
  } catch {
    ElMessage.info("删除操作已取消或失败");
  }
}

async function openVersions(template: PromptTemplateDetail) {
  versionTemplate.value = template;
  versionsVisible.value = true;
  loadingVersions.value = true;
  try {
    versions.value = await fetchPromptTemplateVersions(template.template_id);
  } catch {
    versions.value = [];
    ElMessage.error("模板版本加载失败");
  } finally {
    loadingVersions.value = false;
  }
}

async function rollbackVersion(version: PromptTemplateVersionDetail) {
  if (!versionTemplate.value) {
    return;
  }
  try {
    await rollbackPromptTemplate(versionTemplate.value.template_id, version.version_id);
    ElMessage.success(`已回滚到 v${version.version}`);
    await Promise.all([loadTemplates(), openVersions(versionTemplate.value)]);
  } catch {
    ElMessage.error("版本回滚失败");
  }
}

onMounted(loadTemplates);
</script>
