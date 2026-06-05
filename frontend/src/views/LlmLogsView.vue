<template>
  <section class="settings-page">
    <div class="page-header settings-header">
      <div>
        <h1 class="page-title">调用日志</h1>
        <p class="page-subtitle">查看大模型调用状态、耗时、Token 用量和错误摘要。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadLogs">刷新</el-button>
    </div>

    <section class="settings-panel">
      <div class="template-filters">
        <el-select v-model="filters.task_type" clearable placeholder="任务类型" @change="resetAndLoad">
          <el-option v-for="task in taskOptions" :key="task" :label="task" :value="task" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="调用状态" @change="resetAndLoad">
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-date-picker
          v-model="filters.timeRange"
          type="datetimerange"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DDTHH:mm:ss"
          @change="resetAndLoad"
        />
      </div>

      <el-table v-loading="loading" :data="logs" empty-text="暂无调用日志" @row-click="openLog">
        <el-table-column prop="log_id" label="ID" width="80" />
        <el-table-column prop="task_type" label="任务类型" min-width="210" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latency_ms" label="耗时(ms)" width="110" />
        <el-table-column prop="total_tokens" label="Tokens" width="110" />
        <el-table-column prop="task_id" label="任务ID" width="100" />
        <el-table-column prop="llm_config_id" label="配置ID" width="100" />
        <el-table-column prop="created_at" label="时间" min-width="180" />
      </el-table>

      <div class="table-footer">
        <span class="page-subtitle">共 {{ total }} 条</span>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          layout="prev, pager, next, sizes"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          @change="loadLogs"
        />
      </div>
    </section>

    <el-drawer v-model="detailVisible" title="调用详情" size="680px">
      <section v-if="selectedLog" class="log-detail">
        <div class="log-metrics">
          <el-statistic title="输入 Tokens" :value="selectedLog.input_tokens ?? 0" />
          <el-statistic title="输出 Tokens" :value="selectedLog.output_tokens ?? 0" />
          <el-statistic title="总 Tokens" :value="selectedLog.total_tokens ?? 0" />
          <el-statistic title="耗时 ms" :value="selectedLog.latency_ms ?? 0" />
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="日志 ID">{{ selectedLog.log_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selectedLog.status }}</el-descriptions-item>
          <el-descriptions-item label="任务类型">{{ selectedLog.task_type }}</el-descriptions-item>
          <el-descriptions-item label="任务 ID">{{ selectedLog.task_id || "-" }}</el-descriptions-item>
          <el-descriptions-item label="模型配置">{{ selectedLog.llm_config_id || "-" }}</el-descriptions-item>
          <el-descriptions-item label="提示词模板">{{ selectedLog.prompt_template_id || "-" }}</el-descriptions-item>
        </el-descriptions>
        <div class="log-block">
          <div class="panel-title">请求摘要</div>
          <pre>{{ selectedLog.request_summary || "-" }}</pre>
        </div>
        <div class="log-block">
          <div class="panel-title">响应摘要</div>
          <pre>{{ selectedLog.response_summary || "-" }}</pre>
        </div>
        <div v-if="selectedLog.error_message" class="log-block">
          <div class="panel-title">错误信息</div>
          <pre>{{ selectedLog.error_message }}</pre>
        </div>
      </section>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { onMounted, reactive, ref } from "vue";

import {
  type LlmCallLogDetail,
  type LlmCallLogListItem,
  fetchLlmCallLog,
  fetchLlmCallLogs
} from "@/api/client";

const taskOptions = [
  "story_profile_generation",
  "chapter_summary_generation",
  "style_strategy_generation",
  "scene_plan_generation",
  "script_yaml_generation",
  "yaml_repair"
];

const logs = ref<LlmCallLogListItem[]>([]);
const selectedLog = ref<LlmCallLogDetail | null>(null);
const loading = ref(false);
const detailVisible = ref(false);
const page = ref(1);
const size = ref(20);
const total = ref(0);
const filters = reactive<{
  task_type: string;
  status: string;
  timeRange: [string, string] | null;
}>({
  task_type: "",
  status: "",
  timeRange: null
});

async function loadLogs() {
  loading.value = true;
  try {
    const result = await fetchLlmCallLogs({
      task_type: filters.task_type || undefined,
      status: filters.status || undefined,
      start_time: filters.timeRange?.[0],
      end_time: filters.timeRange?.[1],
      page: page.value,
      size: size.value
    });
    logs.value = result.records;
    total.value = result.total;
  } catch {
    logs.value = [];
    total.value = 0;
    ElMessage.error("调用日志加载失败，请检查后端服务和数据库连接");
  } finally {
    loading.value = false;
  }
}

function resetAndLoad() {
  page.value = 1;
  void loadLogs();
}

async function openLog(log: LlmCallLogListItem) {
  try {
    selectedLog.value = await fetchLlmCallLog(log.log_id);
    detailVisible.value = true;
  } catch {
    ElMessage.error("调用详情加载失败");
  }
}

onMounted(loadLogs);
</script>
