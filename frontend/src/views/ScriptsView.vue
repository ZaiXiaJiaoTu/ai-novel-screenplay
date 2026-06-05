<template>
  <section class="scripts-page">
    <div class="page-header settings-header">
      <div>
        <h1 class="page-title">剧本书架</h1>
        <p class="page-subtitle">创建剧本生成任务，查看生成后的项目和片段，并导出 YAML 或 TXT。</p>
      </div>
      <div class="settings-actions">
        <el-button :icon="Refresh" :loading="loadingProjects" @click="loadProjects">刷新书架</el-button>
        <el-button type="primary" :icon="VideoPlay" @click="openTaskDialog">生成剧本</el-button>
      </div>
    </div>

    <section v-if="currentTask" class="settings-panel task-status-panel">
      <div>
        <div class="panel-title">最近任务 #{{ currentTask.task_id }}</div>
        <div class="task-status-line">
          <el-tag :type="taskStatusType">{{ taskStatusLabel }}</el-tag>
          <span>{{ currentTask.current_step || "等待中" }}</span>
        </div>
      </div>
      <div class="task-progress-block">
        <el-progress :percentage="currentTask.progress" :status="taskProgressStatus" />
        <el-alert
          v-if="currentTask.error_message"
          type="error"
          :title="currentTask.error_message"
          :closable="false"
          show-icon
        />
      </div>
      <div class="settings-actions">
        <el-button :icon="Refresh" :loading="taskActionLoading" @click="refreshTask">刷新任务</el-button>
        <el-button v-if="canCancelTask" :loading="taskActionLoading" @click="cancelTask">取消任务</el-button>
        <el-button v-if="canRetryTask" type="primary" :loading="taskActionLoading" @click="retryTask">
          重新生成
        </el-button>
        <el-button :icon="Document" @click="loadArtifacts">查看中间成果</el-button>
      </div>
    </section>

    <div class="script-workspace">
      <section class="settings-panel">
        <div class="panel-title">项目列表</div>
        <el-table
          v-loading="loadingProjects"
          :data="projects"
          height="420"
          highlight-current-row
          empty-text="暂无剧本项目"
          @row-click="selectProject"
        >
          <el-table-column prop="project_name" label="项目" min-width="180" />
          <el-table-column prop="book_title" label="作品" min-width="150" />
          <el-table-column prop="script_type" label="类型" width="110" />
          <el-table-column prop="segment_count" label="片段" width="80" />
          <el-table-column label="导出" width="140">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="downloadProject(row.project_id, 'txt')">TXT</el-button>
              <el-button link type="primary" @click.stop="downloadProject(row.project_id, 'yaml')">YAML</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="settings-panel">
        <div class="panel-title">片段列表</div>
        <p class="page-subtitle script-selected-title">
          {{ selectedProject ? selectedProject.project_name : "请选择剧本项目" }}
        </p>
        <el-table
          v-loading="loadingSegments"
          :data="segments"
          height="376"
          empty-text="暂无剧本片段"
          @row-click="openSegment"
        >
          <el-table-column prop="segment_name" label="片段" min-width="180" />
          <el-table-column prop="style" label="风格" width="120" />
          <el-table-column prop="scene_count" label="场景" width="80" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="openSegment(row)">编辑</el-button>
              <el-button link type="primary" @click.stop="downloadSegment(row.segment_id, 'yaml')">YAML</el-button>
              <el-button link type="danger" @click.stop="removeSegment(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <el-dialog v-model="taskDialogVisible" title="生成剧本" width="720px">
      <el-form label-position="top">
        <el-form-item label="选择作品">
          <el-select v-model="taskForm.book_id" filterable placeholder="请选择已导入作品">
            <el-option
              v-for="book in books"
              :key="book.book_id"
              :label="`${book.title}（${book.chapter_count} 章）`"
              :value="book.book_id"
            />
          </el-select>
        </el-form-item>
        <div class="settings-form-grid">
          <el-form-item label="剧本类型">
            <el-select v-model="taskForm.script_type">
              <el-option label="短剧" value="short_drama" />
              <el-option label="分镜脚本" value="screenplay" />
              <el-option label="解说脚本" value="narration" />
            </el-select>
          </el-form-item>
          <el-form-item label="风格">
            <el-input v-model="taskForm.style" placeholder="悬疑、轻喜剧、现实主义" />
          </el-form-item>
          <el-form-item label="压缩级别">
            <el-select v-model="taskForm.compression_level">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
            </el-select>
          </el-form-item>
        </div>
        <div class="settings-form-grid">
          <el-form-item label="起始章节">
            <el-input-number v-model="taskForm.start_chapter" :min="1" />
          </el-form-item>
          <el-form-item label="结束章节">
            <el-input-number v-model="taskForm.end_chapter" :min="1" />
          </el-form-item>
          <el-form-item label="目标时长（分钟）">
            <el-input-number v-model="taskForm.target_duration" :min="1" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingTask" @click="createAndStartTask">创建并启动</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="segmentDialogVisible" title="编辑剧本片段" width="920px">
      <el-tabs v-if="segmentDetail" v-model="segmentTab">
        <el-tab-pane label="YAML" name="yaml">
          <el-input v-model="segmentEdit.yaml_content" type="textarea" :rows="18" />
        </el-tab-pane>
        <el-tab-pane label="纯文本" name="text">
          <el-input v-model="segmentEdit.plain_text_content" type="textarea" :rows="18" />
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="segmentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSegment" @click="saveSegment">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="artifactsVisible" title="中间成果" size="520px">
      <el-table :data="artifacts" empty-text="暂无中间成果">
        <el-table-column prop="artifact_type" label="类型" min-width="160" />
        <el-table-column label="版本" width="80">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column label="可编辑" width="90">
          <template #default="{ row }">{{ row.editable ? "是" : "否" }}</template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { Delete, Document, Refresh, VideoPlay } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import {
  type BookListItem,
  type GenerationArtifactListItem,
  type ScriptProjectListItem,
  type ScriptSegmentDetail,
  type ScriptSegmentListItem,
  type ScriptTaskDetail,
  cancelScriptTask,
  createScriptTask,
  deleteScriptSegment,
  fetchBooks,
  fetchScriptProjects,
  fetchScriptSegment,
  fetchScriptSegments,
  fetchScriptTask,
  fetchTaskArtifacts,
  retryScriptTask,
  scriptProjectDownloadUrl,
  scriptSegmentDownloadUrl,
  startScriptTask,
  updateScriptSegmentContent
} from "@/api/client";

const books = ref<BookListItem[]>([]);
const projects = ref<ScriptProjectListItem[]>([]);
const segments = ref<ScriptSegmentListItem[]>([]);
const artifacts = ref<GenerationArtifactListItem[]>([]);
const selectedProject = ref<ScriptProjectListItem | null>(null);
const currentTask = ref<ScriptTaskDetail | null>(null);
const segmentDetail = ref<ScriptSegmentDetail | null>(null);
const loadingProjects = ref(false);
const loadingSegments = ref(false);
const creatingTask = ref(false);
const savingSegment = ref(false);
const taskActionLoading = ref(false);
const taskDialogVisible = ref(false);
const segmentDialogVisible = ref(false);
const artifactsVisible = ref(false);
const segmentTab = ref("yaml");
const taskForm = reactive({
  book_id: undefined as number | undefined,
  script_type: "short_drama",
  style: "",
  compression_level: "medium",
  start_chapter: 1,
  end_chapter: 3,
  target_duration: 5
});
const segmentEdit = reactive({
  yaml_content: "",
  plain_text_content: ""
});

const taskStatusLabels: Record<string, string> = {
  pending: "等待中",
  running: "生成中",
  completed: "已完成",
  failed: "失败",
  canceled: "已取消"
};

const taskStatusLabel = computed(() => {
  if (!currentTask.value) {
    return "";
  }
  return taskStatusLabels[currentTask.value.status] || currentTask.value.status;
});

const taskStatusType = computed(() => {
  if (currentTask.value?.status === "completed") {
    return "success";
  }
  if (currentTask.value?.status === "failed") {
    return "danger";
  }
  if (currentTask.value?.status === "canceled") {
    return "warning";
  }
  return "info";
});

const taskProgressStatus = computed(() => {
  if (currentTask.value?.status === "completed") {
    return "success";
  }
  if (currentTask.value?.status === "failed") {
    return "exception";
  }
  if (currentTask.value?.status === "canceled") {
    return "warning";
  }
  return undefined;
});

const canCancelTask = computed(() => {
  return currentTask.value ? ["pending", "running"].includes(currentTask.value.status) : false;
});

const canRetryTask = computed(() => currentTask.value?.status === "failed");

async function loadBooks() {
  try {
    const result = await fetchBooks();
    books.value = result.records;
  } catch {
    books.value = [];
  }
}

async function loadProjects() {
  loadingProjects.value = true;
  try {
    const result = await fetchScriptProjects({ page: 1, size: 50 });
    projects.value = result.records;
  } catch {
    projects.value = [];
    ElMessage.error("剧本项目加载失败，请检查后端服务和数据库连接");
  } finally {
    loadingProjects.value = false;
  }
}

async function selectProject(project: ScriptProjectListItem) {
  selectedProject.value = project;
  loadingSegments.value = true;
  try {
    segments.value = await fetchScriptSegments(project.project_id);
  } catch {
    segments.value = [];
    ElMessage.error("剧本片段加载失败");
  } finally {
    loadingSegments.value = false;
  }
}

async function openTaskDialog() {
  await loadBooks();
  taskDialogVisible.value = true;
}

async function createAndStartTask() {
  if (!taskForm.book_id) {
    ElMessage.warning("请选择作品");
    return;
  }
  creatingTask.value = true;
  try {
    const created = await createScriptTask({
      book_id: taskForm.book_id,
      project_id: null,
      adapt_scope: {
        type: "chapter_range",
        start_chapter: taskForm.start_chapter,
        end_chapter: taskForm.end_chapter
      },
      generation_config: {
        script_type: taskForm.script_type,
        style: taskForm.style,
        compression_level: taskForm.compression_level,
        target_duration: taskForm.target_duration
      }
    });
    currentTask.value = await startScriptTask(created.task_id);
    ElMessage.success("剧本生成任务已完成");
    taskDialogVisible.value = false;
    await loadProjects();
  } catch {
    ElMessage.error("剧本生成失败，请检查模型配置或后端日志");
  } finally {
    creatingTask.value = false;
  }
}

async function refreshTask() {
  if (!currentTask.value) {
    return;
  }
  taskActionLoading.value = true;
  try {
    currentTask.value = await fetchScriptTask(currentTask.value.task_id);
  } catch {
    ElMessage.error("任务状态刷新失败");
  } finally {
    taskActionLoading.value = false;
  }
}

async function cancelTask() {
  if (!currentTask.value) {
    return;
  }
  try {
    await ElMessageBox.confirm("确定取消当前剧本生成任务？", "取消任务", {
      type: "warning"
    });
    taskActionLoading.value = true;
    currentTask.value = await cancelScriptTask(currentTask.value.task_id);
    ElMessage.success("任务已取消");
  } catch {
    ElMessage.info("取消操作已放弃或失败");
  } finally {
    taskActionLoading.value = false;
  }
}

async function retryTask() {
  if (!currentTask.value) {
    return;
  }
  taskActionLoading.value = true;
  try {
    const pendingTask = await retryScriptTask(currentTask.value.task_id);
    currentTask.value = await startScriptTask(pendingTask.task_id);
    ElMessage.success("任务已重新生成");
    await loadProjects();
  } catch {
    ElMessage.error("重新生成失败，请检查模型配置或后端日志");
  } finally {
    taskActionLoading.value = false;
  }
}

async function loadArtifacts() {
  if (!currentTask.value) {
    return;
  }
  try {
    artifacts.value = await fetchTaskArtifacts(currentTask.value.task_id);
    artifactsVisible.value = true;
  } catch {
    ElMessage.error("中间成果加载失败");
  }
}

async function openSegment(segment: ScriptSegmentListItem) {
  try {
    segmentDetail.value = await fetchScriptSegment(segment.segment_id);
    segmentEdit.yaml_content = segmentDetail.value.yaml_content || "";
    segmentEdit.plain_text_content = segmentDetail.value.plain_text_content || "";
    segmentDialogVisible.value = true;
  } catch {
    ElMessage.error("剧本片段详情加载失败");
  }
}

async function saveSegment() {
  if (!segmentDetail.value) {
    return;
  }
  savingSegment.value = true;
  try {
    const saved = await updateScriptSegmentContent(segmentDetail.value.segment_id, {
      yaml_content: segmentEdit.yaml_content,
      plain_text_content: segmentEdit.plain_text_content
    });
    segmentDetail.value = saved;
    ElMessage.success("片段已保存");
    segmentDialogVisible.value = false;
    if (selectedProject.value) {
      await selectProject(selectedProject.value);
    }
  } catch {
    ElMessage.error("片段保存失败");
  } finally {
    savingSegment.value = false;
  }
}

async function removeSegment(segment: ScriptSegmentListItem) {
  try {
    await ElMessageBox.confirm(`确定删除 ${segment.segment_name}？`, "删除片段", {
      type: "warning"
    });
    await deleteScriptSegment(segment.segment_id);
    ElMessage.success("片段已删除");
    if (selectedProject.value) {
      await selectProject(selectedProject.value);
    }
  } catch {
    ElMessage.info("删除操作已取消或失败");
  }
}

function downloadSegment(segmentId: number, format: "yaml" | "txt") {
  window.open(scriptSegmentDownloadUrl(segmentId, format), "_blank");
}

function downloadProject(projectId: number, format: "yaml" | "txt") {
  window.open(scriptProjectDownloadUrl(projectId, format), "_blank");
}

onMounted(() => {
  void loadProjects();
});
</script>
