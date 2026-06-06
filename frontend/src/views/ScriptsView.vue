<template>
  <section class="scripts-page">
    <div class="page-header books-header">
      <div>
        <h1 class="page-title">剧本书架</h1>
        <p class="page-subtitle">从小说创建改编项目，按剧情事件、人物、分集剧本和导出四个模块推进。</p>
      </div>
      <el-button :icon="Refresh" :loading="loadingProjects" @click="reloadAll">刷新</el-button>
    </div>

    <div class="script-adaptation-layout">
      <aside class="bookshelf-sidebar">
        <div class="bookshelf-sidebar-header">
          <div>
            <div class="panel-title">剧本列表</div>
            <p class="page-subtitle">共 {{ projects.length }} 个项目</p>
          </div>
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">剧本改编</el-button>
        </div>

        <el-scrollbar class="book-list-scroll" v-loading="loadingProjects">
          <button
            v-for="project in projects"
            :key="project.project_id"
            class="book-list-item"
            :class="{ active: selectedProject?.project_id === project.project_id }"
            type="button"
            @click="selectProject(project)"
          >
            <span class="book-title">{{ project.project_name }}</span>
            <span class="book-meta">
              {{ project.book_title }} / {{ typeLabel(project.adaptation_type) }} /
              {{ project.episode_count }} 集
            </span>
            <span class="book-meta">
              事件 {{ project.event_count }} / 人物 {{ project.character_count }}
            </span>
            <span class="script-list-actions">
              <el-button link type="primary" :icon="Setting" @click.stop="openConfigDialog(project)">
                参数
              </el-button>
              <el-button link type="danger" :icon="Delete" @click.stop="removeProject(project)">
                删除
              </el-button>
            </span>
          </button>
          <el-empty v-if="!loadingProjects && projects.length === 0" description="暂无剧本项目" />
        </el-scrollbar>
      </aside>

      <main class="chapter-workspace">
        <div class="chapter-toolbar">
          <div>
            <div class="panel-title">
              {{ selectedProject ? selectedProject.project_name : "改编模块" }}
            </div>
            <p class="page-subtitle">
              {{
                selectedProject
                  ? `${typeLabel(selectedProject.adaptation_type)} / ${selectedProject.episode_duration || "-"} 分钟 / ${pacingLabel(selectedProject.pacing)}`
                  : "请选择左侧剧本项目"
              }}
            </p>
          </div>
          <el-tag v-if="progress" type="info">
            已拆分 {{ progress.split_chapter_count }}/{{ progress.chapter_count }} 章
          </el-tag>
        </div>

        <el-tabs v-model="activeModule" class="script-module-tabs">
          <el-tab-pane label="剧情事件拆分" name="events">
            <section class="module-stack">
              <div class="module-actions">
                <el-button
                  type="primary"
                  :icon="Scissor"
                  :disabled="!selectedProject"
                  :loading="splitting"
                  @click="splitOnce"
                >
                  单次拆分
                </el-button>
                <el-button
                  :icon="DArrowRight"
                  :disabled="!selectedProject || isSplitting"
                  :loading="isSplitting"
                  @click="splitAll"
                >
                  全部拆分
                </el-button>
                <el-button
                  type="warning"
                  :icon="CircleClose"
                  :disabled="!selectedProject || !isSplitting"
                  @click="stopSplit"
                >
                  安全停止拆分
                </el-button>
              </div>

              <div v-if="progress" class="script-progress-row">
                <el-progress :percentage="splitPercent" />
                <span>
                  {{ progress.batch_count }} 个批次 / {{ progress.event_count }} 个事件
                </span>
              </div>

              <el-table :data="batchesWithEvents" empty-text="暂无拆分批次">
                <el-table-column type="expand">
                  <template #default="{ row }">
                    <div class="batch-events-panel">
                      <el-table :data="row.events" empty-text="本批次暂无剧情事件">
                        <el-table-column prop="event_index" label="序号" width="80" />
                        <el-table-column prop="content" label="剧情事件" min-width="360" show-overflow-tooltip />
                        <el-table-column label="来源章节" width="130">
                          <template #default="{ row: event }">
                            {{ event.source_chapter_start }} - {{ event.source_chapter_end }}
                          </template>
                        </el-table-column>
                        <el-table-column label="状态" width="90">
                          <template #default="{ row: event }">
                            <el-tag :type="event.locked ? 'warning' : 'success'">
                              {{ event.locked ? "已锁定" : "可编辑" }}
                            </el-tag>
                          </template>
                        </el-table-column>
                        <el-table-column label="操作" width="150">
                          <template #default="{ row: event }">
                            <el-button link type="primary" :disabled="event.locked" @click="openEventDialog(event)">
                              编辑
                            </el-button>
                            <el-button link type="danger" :disabled="event.locked" @click="removeEvent(event)">
                              删除
                            </el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="batch_index" label="批次" width="90" />
                <el-table-column label="章节范围" width="160">
                  <template #default="{ row }">
                    {{ row.chapter_start_index }} - {{ row.chapter_end_index }}
                  </template>
                </el-table-column>
                <el-table-column prop="event_count" label="事件数" width="100" />
                <el-table-column prop="status" label="状态" width="120" />
              </el-table>
            </section>
          </el-tab-pane>

          <el-tab-pane label="人物" name="characters">
            <el-table :data="characters" empty-text="暂无人物档案">
              <el-table-column prop="name" label="人物" width="180" />
              <el-table-column prop="profile" label="档案" min-width="420" show-overflow-tooltip />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openCharacterDialog(row)">编辑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="剧本生成" name="episodes">
            <div class="episode-workspace">
              <section class="episode-control-panel">
                <el-form label-position="top">
                  <el-form-item label="每集分配剧情事件">
                    <el-input-number v-model="episodeConfig.events_per_episode" :min="1" :max="100" />
                  </el-form-item>
                </el-form>
                <div class="module-actions vertical">
                  <el-button
                    type="primary"
                    :disabled="!selectedProject"
                    :loading="generatingEpisode"
                    @click="generateEpisodeOnce"
                  >
                    单集生成
                  </el-button>
                  <el-button
                    :disabled="!selectedProject || isGeneratingEpisode"
                    :loading="isGeneratingEpisode"
                    @click="generateEpisodesAll"
                  >
                    全部生成
                  </el-button>
                  <el-button type="warning" :disabled="!selectedProject || !isGeneratingEpisode" @click="stopEpisodes">
                    安全停止生成
                  </el-button>
                </div>
                <el-divider />
                <el-table :data="episodes" empty-text="暂无分集剧本" height="360" @row-click="selectEpisode">
                  <el-table-column prop="episode_index" label="集数" width="80" />
                  <el-table-column prop="title" label="标题" min-width="160" />
                  <el-table-column label="事件" width="80">
                    <template #default="{ row }">{{ row.event_ids.length }}</template>
                  </el-table-column>
                </el-table>
              </section>

              <section class="episode-editor-panel">
                <div class="panel-title">
                  {{ selectedEpisode ? selectedEpisode.title : "剧本预览" }}
                </div>
                <el-tabs v-model="episodePreviewTab">
                  <el-tab-pane label="中文表单编辑" name="form">
                    <el-form class="episode-form-editor" label-position="top">
                      <el-form-item label="分集标题">
                        <el-input v-model="episodeEdit.title" :disabled="!selectedEpisode" />
                      </el-form-item>
                      <div class="settings-form-grid">
                        <el-form-item label="剧本内标题">
                          <el-input v-model="episodeForm.metadata.title" :disabled="!selectedEpisode" />
                        </el-form-item>
                        <el-form-item label="来源小说">
                          <el-input v-model="episodeForm.metadata.source_book_title" disabled />
                        </el-form-item>
                        <el-form-item label="目标时长">
                          <el-input-number
                            v-model="episodeForm.metadata.target_duration"
                            :min="1"
                            :max="240"
                            :disabled="!selectedEpisode"
                          />
                        </el-form-item>
                      </div>
                      <div class="episode-form-toolbar">
                        <span class="page-subtitle">场景 {{ episodeForm.scenes.length }} 个</span>
                        <el-button size="small" :disabled="!selectedEpisode" @click="addEpisodeScene">
                          增加场景
                        </el-button>
                      </div>
                      <el-collapse v-model="openSceneNames" class="episode-scene-collapse">
                        <el-collapse-item
                          v-for="(scene, sceneIndex) in episodeForm.scenes"
                          :key="scene.local_id"
                          :name="scene.local_id"
                        >
                          <template #title>
                            {{ scene.scene_id || sceneIndex + 1 }}. {{ scene.scene_title || "未命名场景" }}
                          </template>
                          <div class="settings-form-grid">
                            <el-form-item label="场景编号">
                              <el-input v-model="scene.scene_id" />
                            </el-form-item>
                            <el-form-item label="场景标题">
                              <el-input v-model="scene.scene_title" />
                            </el-form-item>
                            <el-form-item label="地点">
                              <el-input v-model="scene.location" />
                            </el-form-item>
                            <el-form-item label="时间">
                              <el-input v-model="scene.time" />
                            </el-form-item>
                          </div>
                          <el-form-item label="出场人物（逗号分隔）">
                            <el-input v-model="scene.characters_text" />
                          </el-form-item>
                          <el-form-item label="动作描写（每行一条）">
                            <el-input v-model="scene.action_text" type="textarea" :rows="4" />
                          </el-form-item>
                          <el-form-item label="转场">
                            <el-input v-model="scene.transition" />
                          </el-form-item>
                          <div class="episode-form-toolbar">
                            <span class="page-subtitle">对白 {{ scene.dialogue.length }} 条</span>
                            <div>
                              <el-button size="small" @click="addDialogue(scene)">增加对白</el-button>
                              <el-button size="small" type="danger" @click="removeScene(sceneIndex)">
                                删除场景
                              </el-button>
                            </div>
                          </div>
                          <div
                            v-for="(dialogue, dialogueIndex) in scene.dialogue"
                            :key="dialogue.local_id"
                            class="dialogue-row"
                          >
                            <el-input v-model="dialogue.speaker" placeholder="说话人" />
                            <el-input v-model="dialogue.line" placeholder="台词" />
                            <el-button link type="danger" @click="removeDialogue(scene, dialogueIndex)">
                              删除
                            </el-button>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
                    </el-form>
                  </el-tab-pane>
                  <el-tab-pane label="YAML源码编辑" name="yaml">
                    <el-input
                      v-model="episodeEdit.yaml_content"
                      type="textarea"
                      :rows="18"
                      :disabled="!selectedEpisode"
                    />
                  </el-tab-pane>
                </el-tabs>
                <div class="module-actions">
                  <el-button
                    type="primary"
                    :disabled="!selectedEpisode"
                    :loading="savingEpisode"
                    @click="saveEpisode"
                  >
                    保存修改
                  </el-button>
                </div>
              </section>
            </div>
          </el-tab-pane>

          <el-tab-pane label="剧本导出" name="export">
            <section class="module-stack">
              <div class="module-actions">
                <el-select v-model="exportFormat" style="width: 140px">
                  <el-option label="YAML" value="yaml" />
                  <el-option label="TXT" value="txt" />
                </el-select>
                <el-button
                  type="primary"
                  :disabled="!selectedEpisode"
                  :icon="Download"
                  @click="downloadEpisode"
                >
                  分集导出
                </el-button>
                <el-button
                  :disabled="!selectedProject"
                  :icon="Download"
                  @click="downloadAllEpisodes"
                >
                  全部导出
                </el-button>
              </div>
              <el-table :data="episodes" empty-text="暂无可导出的剧集">
                <el-table-column prop="episode_index" label="集数" width="90" />
                <el-table-column prop="title" label="标题" min-width="220" />
                <el-table-column prop="status" label="状态" width="100" />
                <el-table-column label="导出" width="150">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="downloadEpisodeById(row.episode_id, 'yaml')">
                      YAML
                    </el-button>
                    <el-button link type="primary" @click="downloadEpisodeById(row.episode_id, 'txt')">
                      TXT
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </el-tab-pane>
        </el-tabs>
      </main>
    </div>

    <el-dialog v-model="projectDialogVisible" :title="editingProject ? '参数配置' : '剧本改编'" width="720px">
      <el-form label-position="top">
        <el-form-item v-if="!editingProject" label="选择小说">
          <el-select v-model="projectForm.book_id" filterable>
            <el-option
              v-for="book in books"
              :key="book.book_id"
              :label="`${book.title} / ${book.chapter_count} 章`"
              :value="book.book_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="剧本名称">
          <el-input v-model="projectForm.project_name" maxlength="80" show-word-limit />
        </el-form-item>
        <div class="settings-form-grid">
          <el-form-item label="改编类型">
            <el-select v-model="projectForm.adaptation_type" :disabled="Boolean(editingProject)">
              <el-option label="电视剧" value="tv" />
              <el-option label="短剧" value="short_drama" />
              <el-option label="动画" value="animation" />
              <el-option label="广播剧" value="audio_drama" />
            </el-select>
          </el-form-item>
          <el-form-item label="单集时长">
            <el-input-number v-model="projectForm.episode_duration" :min="1" :max="240" />
          </el-form-item>
          <el-form-item label="剧情节奏">
            <el-select v-model="projectForm.pacing">
              <el-option label="快" value="fast" />
              <el-option label="适中" value="medium" />
              <el-option label="慢" value="slow" />
            </el-select>
          </el-form-item>
        </div>
        <div class="settings-form-grid">
          <el-form-item label="场景切换频率">
            <el-select v-model="projectForm.scene_frequency">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="对话密度">
            <el-select v-model="projectForm.dialogue_density">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="每集剧情事件数">
            <el-input-number v-model="projectForm.events_per_episode" :min="1" :max="100" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="projectDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingProject" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="eventDialogVisible" title="编辑剧情事件" width="680px">
      <el-input v-model="eventForm.content" type="textarea" :rows="8" />
      <template #footer>
        <el-button @click="eventDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingEvent" @click="saveEvent">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="characterDialogVisible" title="编辑人物档案" width="680px">
      <el-form label-position="top">
        <el-form-item label="人物名称">
          <el-input v-model="characterForm.name" />
        </el-form-item>
        <el-form-item label="人物档案">
          <el-input v-model="characterForm.profile" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="characterDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingCharacter" @click="saveCharacter">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import {
  CircleClose,
  DArrowRight,
  Delete,
  Download,
  Plus,
  Refresh,
  Scissor,
  Setting
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";

import {
  type AdaptationType,
  type BookListItem,
  type DensityLevel,
  type PacingLevel,
  type ScriptAdaptationProject,
  type ScriptCharacterDetail,
  type ScriptEpisodeDetail,
  type ScriptEventBatchDetail,
  type ScriptPlotEventDetail,
  type ScriptWorkflowProgress,
  createScriptAdaptation,
  deleteScriptAdaptation,
  deleteScriptPlotEvent,
  fetchBooks,
  fetchScriptAdaptationProgress,
  fetchScriptAdaptations,
  fetchScriptCharacters,
  fetchScriptEpisodes,
  fetchScriptEventBatches,
  fetchScriptPlotEvents,
  generateScriptEpisodeOnce,
  generateScriptEpisodesAll,
  scriptAdaptationDownloadUrl,
  scriptAdaptationEpisodeDownloadUrl,
  splitScriptEventsAll,
  splitScriptEventsOnce,
  stopScriptEpisodeGeneration,
  stopScriptEventSplit,
  updateScriptAdaptationConfig,
  updateScriptCharacter,
  updateScriptEpisode,
  updateScriptPlotEvent
} from "@/api/client";

const projects = ref<ScriptAdaptationProject[]>([]);
const books = ref<BookListItem[]>([]);
const selectedProject = ref<ScriptAdaptationProject | null>(null);
const progress = ref<ScriptWorkflowProgress | null>(null);
const batches = ref<ScriptEventBatchDetail[]>([]);
const events = ref<ScriptPlotEventDetail[]>([]);
const characters = ref<ScriptCharacterDetail[]>([]);
const episodes = ref<ScriptEpisodeDetail[]>([]);
const selectedEpisode = ref<ScriptEpisodeDetail | null>(null);
const editingProject = ref<ScriptAdaptationProject | null>(null);
const editingEvent = ref<ScriptPlotEventDetail | null>(null);
const editingCharacter = ref<ScriptCharacterDetail | null>(null);
const activeModule = ref("events");
const episodePreviewTab = ref<"form" | "yaml">("form");
const exportFormat = ref<"yaml" | "txt">("yaml");
const openSceneNames = ref<string[]>([]);
const loadingProjects = ref(false);
const savingProject = ref(false);
const splitting = ref(false);
const generatingEpisode = ref(false);
const savingEpisode = ref(false);
const savingEvent = ref(false);
const savingCharacter = ref(false);
const projectDialogVisible = ref(false);
const eventDialogVisible = ref(false);
const characterDialogVisible = ref(false);
let workflowPoller: number | undefined;

const projectForm = reactive({
  book_id: undefined as number | undefined,
  project_name: "",
  adaptation_type: "short_drama" as AdaptationType,
  episode_duration: 10,
  pacing: "medium" as PacingLevel,
  scene_frequency: "medium" as DensityLevel,
  dialogue_density: "medium" as DensityLevel,
  events_per_episode: 10
});
const episodeConfig = reactive({
  events_per_episode: 10
});
const episodeEdit = reactive({
  title: "",
  yaml_content: "",
  yaml_payload: null as Record<string, unknown> | null
});
type EpisodeDialogueForm = {
  local_id: string;
  speaker: string;
  line: string;
};
type EpisodeSceneForm = {
  local_id: string;
  scene_id: string;
  scene_title: string;
  source_events: unknown[];
  location: string;
  time: string;
  characters_text: string;
  action_text: string;
  transition: string;
  dialogue: EpisodeDialogueForm[];
};
const episodeForm = reactive({
  metadata: {
    title: "",
    source_book_title: "",
    script_type: "",
    target_duration: null as number | null
  },
  scenes: [] as EpisodeSceneForm[]
});
const eventForm = reactive({ content: "" });
const characterForm = reactive({ name: "", profile: "" });

const splitPercent = computed(() => {
  if (!progress.value || progress.value.chapter_count === 0) {
    return 0;
  }
  return Math.round((progress.value.split_chapter_count / progress.value.chapter_count) * 100);
});
const isSplitting = computed(() => splitting.value || progress.value?.split_status === "running");
const isGeneratingEpisode = computed(
  () => generatingEpisode.value || progress.value?.generation_status === "running"
);
const batchesWithEvents = computed(() =>
  batches.value.map((batch) => ({
    ...batch,
    events: events.value.filter((event) => event.batch_id === batch.batch_id)
  }))
);

function typeLabel(type: string) {
  return (
    {
      tv: "电视剧",
      short_drama: "短剧",
      animation: "动画",
      audio_drama: "广播剧"
    }[type] || type
  );
}

function pacingLabel(value: string) {
  return ({ fast: "快", medium: "适中", slow: "慢" }[value] || value);
}

async function loadBooks() {
  const result = await fetchBooks();
  books.value = result.records;
}

async function loadProjects() {
  loadingProjects.value = true;
  try {
    const result = await fetchScriptAdaptations({ page: 1, size: 100 });
    projects.value = result.records;
    if (!selectedProject.value && projects.value.length > 0) {
      await selectProject(projects.value[0]);
    }
  } catch {
    projects.value = [];
    ElMessage.error("剧本列表加载失败");
  } finally {
    loadingProjects.value = false;
  }
}

async function reloadAll() {
  await loadProjects();
  if (selectedProject.value) {
    await loadProjectData(selectedProject.value.project_id);
  }
}

async function selectProject(project: ScriptAdaptationProject) {
  selectedProject.value = project;
  episodeConfig.events_per_episode = project.events_per_episode;
  await loadProjectData(project.project_id);
}

async function loadProjectData(projectId: number) {
  const [nextProgress, nextBatches, nextEvents, nextCharacters, nextEpisodes] =
    await Promise.all([
      fetchScriptAdaptationProgress(projectId),
      fetchScriptEventBatches(projectId),
      fetchScriptPlotEvents(projectId),
      fetchScriptCharacters(projectId),
      fetchScriptEpisodes(projectId)
    ]);
  progress.value = nextProgress;
  batches.value = nextBatches;
  events.value = nextEvents;
  characters.value = nextCharacters;
  episodes.value = nextEpisodes;
  selectedEpisode.value = nextEpisodes[0] ?? null;
  applyEpisodeEdit(selectedEpisode.value);
  syncWorkflowPolling();
}

async function openCreateDialog() {
  await loadBooks();
  editingProject.value = null;
  Object.assign(projectForm, {
    book_id: books.value[0]?.book_id,
    project_name: "",
    adaptation_type: "short_drama",
    episode_duration: 10,
    pacing: "medium",
    scene_frequency: "medium",
    dialogue_density: "medium",
    events_per_episode: 10
  });
  projectDialogVisible.value = true;
}

function openConfigDialog(project: ScriptAdaptationProject) {
  editingProject.value = project;
  Object.assign(projectForm, {
    book_id: project.book_id,
    project_name: project.project_name,
    adaptation_type: project.adaptation_type,
    episode_duration: project.episode_duration || 10,
    pacing: project.pacing,
    scene_frequency: project.scene_frequency,
    dialogue_density: project.dialogue_density,
    events_per_episode: project.events_per_episode
  });
  projectDialogVisible.value = true;
}

async function saveProject() {
  if (!projectForm.project_name.trim()) {
    ElMessage.warning("请填写剧本名称");
    return;
  }
  savingProject.value = true;
  try {
    if (editingProject.value) {
      await updateScriptAdaptationConfig(editingProject.value.project_id, {
        project_name: projectForm.project_name.trim(),
        episode_duration: projectForm.episode_duration,
        pacing: projectForm.pacing,
        scene_frequency: projectForm.scene_frequency,
        dialogue_density: projectForm.dialogue_density,
        events_per_episode: projectForm.events_per_episode
      });
      ElMessage.success("参数已保存");
    } else {
      if (!projectForm.book_id) {
        ElMessage.warning("请选择小说");
        return;
      }
      await createScriptAdaptation({
        book_id: projectForm.book_id,
        project_name: projectForm.project_name.trim(),
        adaptation_type: projectForm.adaptation_type,
        episode_duration: projectForm.episode_duration,
        pacing: projectForm.pacing,
        scene_frequency: projectForm.scene_frequency,
        dialogue_density: projectForm.dialogue_density,
        events_per_episode: projectForm.events_per_episode
      });
      ElMessage.success("剧本项目已创建");
    }
    projectDialogVisible.value = false;
    await loadProjects();
  } catch {
    ElMessage.error("剧本项目保存失败");
  } finally {
    savingProject.value = false;
  }
}

async function removeProject(project: ScriptAdaptationProject) {
  await ElMessageBox.confirm(`确定删除「${project.project_name}」以及全部改编数据吗？`, "删除剧本", {
    type: "warning"
  });
  await deleteScriptAdaptation(project.project_id);
  ElMessage.success("剧本已删除");
  if (selectedProject.value?.project_id === project.project_id) {
    selectedProject.value = null;
    progress.value = null;
    batches.value = [];
    events.value = [];
    characters.value = [];
    episodes.value = [];
  }
  await loadProjects();
}

async function splitOnce() {
  if (!selectedProject.value) return;
  splitting.value = true;
  try {
    progress.value = await splitScriptEventsOnce(selectedProject.value.project_id);
    await reloadSelectedData();
    ElMessage.success("已完成一次剧情拆分");
  } catch {
    ElMessage.error("剧情拆分失败");
  } finally {
    splitting.value = false;
  }
}

async function splitAll() {
  if (!selectedProject.value) return;
  splitting.value = true;
  try {
    progress.value = await splitScriptEventsAll(selectedProject.value.project_id);
    await reloadSelectedData();
    startWorkflowPolling();
    ElMessage.success("已开始全部拆分，可随时安全停止");
  } catch {
    ElMessage.error("启动全部拆分失败");
  } finally {
    splitting.value = false;
  }
}

async function stopSplit() {
  if (!selectedProject.value) return;
  progress.value = await stopScriptEventSplit(selectedProject.value.project_id);
  await reloadSelectedData();
  startWorkflowPolling();
  ElMessage.success("已请求安全停止拆分，当前批次完成后不会再调用模型");
}

async function reloadSelectedData() {
  if (!selectedProject.value) return;
  await loadProjectData(selectedProject.value.project_id);
  const result = await fetchScriptAdaptations({ page: 1, size: 100 });
  projects.value = result.records;
  selectedProject.value =
    projects.value.find((item) => item.project_id === selectedProject.value?.project_id) ??
    selectedProject.value;
}

function openEventDialog(event: ScriptPlotEventDetail) {
  editingEvent.value = event;
  eventForm.content = event.content;
  eventDialogVisible.value = true;
}

async function saveEvent() {
  if (!editingEvent.value) return;
  savingEvent.value = true;
  try {
    await updateScriptPlotEvent(editingEvent.value.event_id, {
      content: eventForm.content.trim()
    });
    eventDialogVisible.value = false;
    await reloadSelectedData();
  } finally {
    savingEvent.value = false;
  }
}

async function removeEvent(event: ScriptPlotEventDetail) {
  await ElMessageBox.confirm("确定删除这个剧情事件吗？", "删除剧情事件", { type: "warning" });
  await deleteScriptPlotEvent(event.event_id);
  await reloadSelectedData();
}

function openCharacterDialog(character: ScriptCharacterDetail) {
  editingCharacter.value = character;
  characterForm.name = character.name;
  characterForm.profile = character.profile;
  characterDialogVisible.value = true;
}

async function saveCharacter() {
  if (!editingCharacter.value) return;
  savingCharacter.value = true;
  try {
    await updateScriptCharacter(editingCharacter.value.character_id, {
      name: characterForm.name.trim(),
      profile: characterForm.profile
    });
    characterDialogVisible.value = false;
    await reloadSelectedData();
  } finally {
    savingCharacter.value = false;
  }
}

async function generateEpisodeOnce() {
  if (!selectedProject.value) return;
  generatingEpisode.value = true;
  try {
    await generateScriptEpisodeOnce(selectedProject.value.project_id, {
      events_per_episode: episodeConfig.events_per_episode
    });
    await reloadSelectedData();
    ElMessage.success("单集剧本已生成");
  } catch {
    ElMessage.error("单集生成失败，可能是可用剧情事件不足");
  } finally {
    generatingEpisode.value = false;
  }
}

async function generateEpisodesAll() {
  if (!selectedProject.value) return;
  generatingEpisode.value = true;
  try {
    progress.value = await generateScriptEpisodesAll(selectedProject.value.project_id, {
      events_per_episode: episodeConfig.events_per_episode
    });
    await reloadSelectedData();
    startWorkflowPolling();
    ElMessage.success("已开始全部生成，可随时安全停止");
  } catch {
    ElMessage.error("启动全部生成失败");
  } finally {
    generatingEpisode.value = false;
  }
}

async function stopEpisodes() {
  if (!selectedProject.value) return;
  progress.value = await stopScriptEpisodeGeneration(selectedProject.value.project_id);
  await reloadSelectedData();
  startWorkflowPolling();
  ElMessage.success("已请求安全停止生成，当前剧集完成后不会再调用模型");
}

function startWorkflowPolling() {
  if (workflowPoller !== undefined) {
    window.clearInterval(workflowPoller);
  }
  workflowPoller = window.setInterval(() => {
    void pollWorkflow();
  }, 2500);
}

function stopWorkflowPolling() {
  if (workflowPoller !== undefined) {
    window.clearInterval(workflowPoller);
    workflowPoller = undefined;
  }
}

function syncWorkflowPolling() {
  if (progress.value?.split_status === "running" || progress.value?.generation_status === "running") {
    startWorkflowPolling();
  } else {
    stopWorkflowPolling();
  }
}

async function pollWorkflow() {
  if (!selectedProject.value) {
    stopWorkflowPolling();
    return;
  }
  await reloadSelectedData();
  if (progress.value?.split_status !== "running" && progress.value?.generation_status !== "running") {
    stopWorkflowPolling();
  }
}

function selectEpisode(episode: ScriptEpisodeDetail) {
  selectedEpisode.value = episode;
  applyEpisodeEdit(episode);
}

function applyEpisodeEdit(episode: ScriptEpisodeDetail | null) {
  episodeEdit.title = episode?.title || "";
  episodeEdit.yaml_content = episode?.yaml_content || "";
  episodeEdit.yaml_payload = episode?.yaml_payload || null;
  applyEpisodeForm(episodeEdit.yaml_payload);
}

async function saveEpisode() {
  if (!selectedEpisode.value) return;
  savingEpisode.value = true;
  try {
    const payload =
      episodePreviewTab.value === "form"
        ? {
            title: episodeEdit.title,
            yaml_payload: buildEpisodePayloadFromForm()
          }
        : {
            title: episodeEdit.title,
            yaml_content: episodeEdit.yaml_content
          };
    selectedEpisode.value = await updateScriptEpisode(selectedEpisode.value.episode_id, {
      ...payload
    });
    await reloadSelectedData();
    ElMessage.success("剧本已保存");
  } finally {
    savingEpisode.value = false;
  }
}

function recordOf(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function arrayOf(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function stringListText(value: unknown) {
  return arrayOf(value).map(String).join("\n");
}

function commaListText(value: unknown) {
  return arrayOf(value).map(String).join("，");
}

function splitLines(value: string) {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitComma(value: string) {
  return value
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function nextLocalId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function applyEpisodeForm(payload: Record<string, unknown> | null) {
  const script = recordOf(payload?.script);
  const metadata = recordOf(script.metadata);
  episodeForm.metadata.title = String(metadata.title || "");
  episodeForm.metadata.source_book_title = String(metadata.source_book_title || selectedProject.value?.book_title || "");
  episodeForm.metadata.script_type = String(metadata.script_type || selectedProject.value?.adaptation_type || "");
  episodeForm.metadata.target_duration =
    typeof metadata.target_duration === "number"
      ? metadata.target_duration
      : selectedProject.value?.episode_duration || null;
  episodeForm.scenes.splice(
    0,
    episodeForm.scenes.length,
    ...arrayOf(script.scenes).map((item, index) => {
      const scene = recordOf(item);
      return {
        local_id: nextLocalId("scene"),
        scene_id: String(scene.scene_id || index + 1),
        scene_title: String(scene.scene_title || ""),
        source_events: arrayOf(scene.source_events),
        location: String(scene.location || ""),
        time: String(scene.time || ""),
        characters_text: commaListText(scene.characters),
        action_text: stringListText(scene.action),
        transition: String(scene.transition || ""),
        dialogue: arrayOf(scene.dialogue).map((dialogue) => {
          const row = recordOf(dialogue);
          return {
            local_id: nextLocalId("dialogue"),
            speaker: String(row.speaker || ""),
            line: String(row.line || "")
          };
        })
      };
    })
  );
  openSceneNames.value = episodeForm.scenes.slice(0, 2).map((scene) => scene.local_id);
}

function buildEpisodePayloadFromForm(): Record<string, unknown> {
  const existingScript = recordOf(episodeEdit.yaml_payload?.script);
  const existingMetadata = recordOf(existingScript.metadata);
  return {
    script: {
      ...existingScript,
      metadata: {
        ...existingMetadata,
        episode_index: selectedEpisode.value?.episode_index,
        title: episodeForm.metadata.title || episodeEdit.title,
        source_book_title: episodeForm.metadata.source_book_title || selectedProject.value?.book_title,
        script_type: episodeForm.metadata.script_type || selectedProject.value?.adaptation_type,
        target_duration: episodeForm.metadata.target_duration || selectedProject.value?.episode_duration
      },
      scenes: episodeForm.scenes.map((scene) => ({
        scene_id: scene.scene_id,
        scene_title: scene.scene_title,
        source_events: scene.source_events,
        location: scene.location,
        time: scene.time,
        characters: splitComma(scene.characters_text),
        action: splitLines(scene.action_text),
        dialogue: scene.dialogue
          .filter((dialogue) => dialogue.speaker.trim() || dialogue.line.trim())
          .map((dialogue) => ({
            speaker: dialogue.speaker.trim(),
            line: dialogue.line.trim()
          })),
        transition: scene.transition
      }))
    }
  };
}

function addEpisodeScene() {
  const scene: EpisodeSceneForm = {
    local_id: nextLocalId("scene"),
    scene_id: String(episodeForm.scenes.length + 1),
    scene_title: "",
    source_events: [],
    location: "",
    time: "",
    characters_text: "",
    action_text: "",
    transition: "",
    dialogue: []
  };
  episodeForm.scenes.push(scene);
  openSceneNames.value = [...openSceneNames.value, scene.local_id];
}

function removeScene(index: number) {
  episodeForm.scenes.splice(index, 1);
}

function addDialogue(scene: EpisodeSceneForm) {
  scene.dialogue.push({
    local_id: nextLocalId("dialogue"),
    speaker: "",
    line: ""
  });
}

function removeDialogue(scene: EpisodeSceneForm, index: number) {
  scene.dialogue.splice(index, 1);
}

function downloadEpisode() {
  if (!selectedEpisode.value) return;
  downloadEpisodeById(selectedEpisode.value.episode_id, exportFormat.value);
}

function downloadEpisodeById(episodeId: number, format: "yaml" | "txt") {
  window.open(scriptAdaptationEpisodeDownloadUrl(episodeId, format), "_blank");
}

function downloadAllEpisodes() {
  if (!selectedProject.value) return;
  window.open(scriptAdaptationDownloadUrl(selectedProject.value.project_id, exportFormat.value), "_blank");
}

onMounted(() => {
  void loadProjects();
});

onUnmounted(() => {
  stopWorkflowPolling();
});
</script>
