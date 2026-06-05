<template>
  <section class="books-page">
    <div class="page-header books-header">
      <div>
        <h1 class="page-title">待选书架</h1>
        <p class="page-subtitle">导入小说，查看章节，并生成章节摘要与故事设定档案。</p>
      </div>
      <el-button :icon="Refresh" :loading="loadingBooks" @click="loadBooks">刷新</el-button>
    </div>

    <div class="book-workspace">
      <section class="book-import-panel">
        <el-tabs v-model="activeImportTab">
          <el-tab-pane label="粘贴文本" name="text">
            <el-form label-position="top">
              <el-form-item label="作品名称">
                <el-input v-model="textForm.title" maxlength="80" show-word-limit />
              </el-form-item>
              <el-form-item label="小说正文">
                <el-input
                  v-model="textForm.content"
                  type="textarea"
                  :rows="10"
                  placeholder="粘贴包含章节标题的小说正文"
                />
              </el-form-item>
              <el-button
                type="primary"
                :icon="Upload"
                :loading="creatingBook"
                @click="submitTextBook"
              >
                导入文本
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="上传文件" name="file">
            <el-form label-position="top">
              <el-form-item label="作品名称">
                <el-input
                  v-model="fileTitle"
                  maxlength="80"
                  placeholder="可选，默认使用文件名"
                  show-word-limit
                />
              </el-form-item>
              <el-upload
                drag
                :auto-upload="false"
                :limit="1"
                :on-change="selectFile"
                :on-remove="clearFile"
                accept=".txt"
              >
                <el-icon class="upload-icon"><UploadFilled /></el-icon>
                <div>拖拽 txt 文件到这里，或点击选择</div>
              </el-upload>
              <el-button
                class="upload-action"
                type="primary"
                :icon="Upload"
                :disabled="!selectedFile"
                :loading="creatingBook"
                @click="submitFileBook"
              >
                上传文件
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </section>

      <section class="book-list-panel">
        <div class="panel-title">作品列表</div>
        <el-table
          v-loading="loadingBooks"
          :data="books"
          height="360"
          highlight-current-row
          @row-click="selectBook"
        >
          <el-table-column prop="title" label="作品" min-width="180" />
          <el-table-column prop="novel_type" label="篇幅" width="88" />
          <el-table-column prop="chapter_count" label="章节" width="88" />
          <el-table-column prop="word_count" label="字数" width="100" />
          <el-table-column label="设定" width="100">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="openStoryProfile(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <section class="chapter-panel">
      <div class="chapter-toolbar">
        <div>
          <div class="panel-title">章节与摘要</div>
          <p class="page-subtitle">
            {{ selectedBook ? selectedBook.title : "请选择一部作品" }}
          </p>
        </div>
        <div class="settings-actions">
          <el-button
            :icon="Notebook"
            :disabled="!selectedBook"
            :loading="loadingProfile"
            @click="selectedBook && openStoryProfile(selectedBook)"
          >
            故事设定
          </el-button>
          <el-button
            type="primary"
            :icon="DocumentChecked"
            :disabled="!selectedBook"
            :loading="generatingSummaries"
            @click="runChapterSummaryGeneration"
          >
            生成章节摘要
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loadingChapters"
        :data="chapters"
        empty-text="暂无章节"
        @row-click="loadSummary"
      >
        <el-table-column prop="chapter_index" label="序号" width="80" />
        <el-table-column prop="title" label="章节标题" min-width="220" />
        <el-table-column prop="word_count" label="字数" width="100" />
        <el-table-column label="摘要" min-width="260">
          <template #default="{ row }">
            <span>{{ summaryMap[row.chapter_id]?.summary || "点击查看摘要" }}</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="profileVisible" title="故事设定档案" size="720px">
      <section v-if="profileBook" class="profile-drawer">
        <div class="profile-toolbar">
          <div>
            <div class="panel-title">{{ profileBook.title }}</div>
            <p class="page-subtitle">
              v{{ profileForm.version || 1 }} / {{ profileForm.confirmed ? "已确认" : "未确认" }}
            </p>
          </div>
          <div class="settings-actions">
            <el-button :loading="generatingProfile" @click="runStoryProfileGeneration">
              AI 生成设定
            </el-button>
            <el-button type="primary" :loading="savingProfile" @click="saveStoryProfile">
              保存
            </el-button>
          </div>
        </div>

        <el-form label-position="top">
          <div class="settings-form-grid">
            <el-form-item label="标题">
              <el-input v-model="profileForm.title" />
            </el-form-item>
            <el-form-item label="类型">
              <el-input v-model="profileForm.genre" />
            </el-form-item>
            <el-form-item label="基调">
              <el-input v-model="profileForm.tone" />
            </el-form-item>
          </div>
          <el-form-item label="故事概述">
            <el-input v-model="profileForm.overview" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="世界观设定">
            <el-input v-model="profileForm.world_setting" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item label="核心冲突">
            <el-input v-model="profileForm.main_conflict" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="人物">
            <el-input v-model="profileJson.characters" type="textarea" :rows="5" />
          </el-form-item>
          <el-form-item label="关键事件">
            <el-input v-model="profileJson.key_events" type="textarea" :rows="5" />
          </el-form-item>
          <el-form-item label="线索">
            <el-input v-model="profileJson.clues" type="textarea" :rows="4" />
          </el-form-item>
          <el-checkbox v-model="profileForm.confirmed">确认该设定档案</el-checkbox>
        </el-form>
      </section>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import {
  DocumentChecked,
  Notebook,
  Refresh,
  Upload,
  UploadFilled
} from "@element-plus/icons-vue";
import { ElMessage, type UploadFile } from "element-plus";
import { computed, onMounted, reactive, ref } from "vue";

import {
  type BookListItem,
  type ChapterListItem,
  type ChapterSummaryDetail,
  type StoryProfileDetail,
  createBookFromText,
  fetchBookChapters,
  fetchBooks,
  fetchChapterSummary,
  fetchStoryProfile,
  generateChapterSummaries,
  generateStoryProfile,
  updateStoryProfile,
  uploadBook
} from "@/api/client";

const activeImportTab = ref("text");
const books = ref<BookListItem[]>([]);
const chapters = ref<ChapterListItem[]>([]);
const selectedBook = ref<BookListItem | null>(null);
const profileBook = ref<BookListItem | null>(null);
const selectedFile = ref<File | null>(null);
const fileTitle = ref("");
const loadingBooks = ref(false);
const loadingChapters = ref(false);
const creatingBook = ref(false);
const generatingSummaries = ref(false);
const loadingProfile = ref(false);
const generatingProfile = ref(false);
const savingProfile = ref(false);
const profileVisible = ref(false);
const summaries = ref<ChapterSummaryDetail[]>([]);
const textForm = reactive({
  title: "",
  content: ""
});
const profileForm = reactive({
  profile_id: 0,
  version: 1,
  title: "",
  genre: "",
  overview: "",
  world_setting: "",
  main_conflict: "",
  tone: "",
  confirmed: false
});
const profileJson = reactive({
  characters: "[]",
  key_events: "[]",
  clues: "[]"
});

const summaryMap = computed(() =>
  Object.fromEntries(summaries.value.map((item) => [item.chapter_id, item]))
);

function stringifyJson(value: unknown) {
  return JSON.stringify(value ?? [], null, 2);
}

function parseJsonArray(value: string, fieldName: string) {
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    throw new Error(`${fieldName} 必须是合法 JSON 数组`);
  }
}

function applyProfile(profile: StoryProfileDetail) {
  Object.assign(profileForm, {
    profile_id: profile.profile_id,
    version: profile.version,
    title: profile.title || "",
    genre: profile.genre || "",
    overview: profile.overview || "",
    world_setting: profile.world_setting || "",
    main_conflict: profile.main_conflict || "",
    tone: profile.tone || "",
    confirmed: profile.confirmed
  });
  profileJson.characters = stringifyJson(profile.characters);
  profileJson.key_events = stringifyJson(profile.key_events);
  profileJson.clues = stringifyJson(profile.clues);
}

async function loadBooks() {
  loadingBooks.value = true;
  try {
    const result = await fetchBooks();
    books.value = result.records;
  } catch {
    books.value = [];
    ElMessage.error("作品列表加载失败，请检查后端服务和数据库连接");
  } finally {
    loadingBooks.value = false;
  }
}

async function selectBook(book: BookListItem) {
  selectedBook.value = book;
  summaries.value = [];
  loadingChapters.value = true;
  try {
    chapters.value = await fetchBookChapters(book.book_id);
  } catch {
    chapters.value = [];
    ElMessage.error("章节列表加载失败");
  } finally {
    loadingChapters.value = false;
  }
}

async function submitTextBook() {
  if (!textForm.title.trim() || !textForm.content.trim()) {
    ElMessage.warning("请填写作品名称和小说正文");
    return;
  }
  creatingBook.value = true;
  try {
    const result = await createBookFromText({
      title: textForm.title.trim(),
      content: textForm.content
    });
    ElMessage.success("导入成功");
    textForm.title = "";
    textForm.content = "";
    await loadBooks();
    const created = books.value.find((item) => item.book_id === result.book_id);
    if (created) {
      await selectBook(created);
    }
  } catch {
    ElMessage.error("文本导入失败");
  } finally {
    creatingBook.value = false;
  }
}

function selectFile(uploadFile: UploadFile) {
  selectedFile.value = uploadFile.raw ?? null;
}

function clearFile() {
  selectedFile.value = null;
}

async function submitFileBook() {
  if (!selectedFile.value) {
    ElMessage.warning("请选择 txt 文件");
    return;
  }
  creatingBook.value = true;
  try {
    const result = await uploadBook(selectedFile.value, fileTitle.value);
    ElMessage.success("上传成功");
    fileTitle.value = "";
    selectedFile.value = null;
    await loadBooks();
    const created = books.value.find((item) => item.book_id === result.book_id);
    if (created) {
      await selectBook(created);
    }
  } catch {
    ElMessage.error("文件上传失败");
  } finally {
    creatingBook.value = false;
  }
}

async function runChapterSummaryGeneration() {
  if (!selectedBook.value) {
    return;
  }
  generatingSummaries.value = true;
  try {
    const result = await generateChapterSummaries(selectedBook.value.book_id);
    summaries.value = result.summaries;
    ElMessage.success(`已生成 ${result.generated_count} 个章节摘要`);
  } catch {
    ElMessage.error("章节摘要生成失败");
  } finally {
    generatingSummaries.value = false;
  }
}

async function loadSummary(chapter: ChapterListItem) {
  try {
    const summary = await fetchChapterSummary(chapter.chapter_id);
    summaries.value = [
      ...summaries.value.filter((item) => item.chapter_id !== chapter.chapter_id),
      summary
    ];
  } catch {
    ElMessage.info("该章节还没有摘要");
  }
}

async function openStoryProfile(book: BookListItem) {
  profileBook.value = book;
  profileVisible.value = true;
  loadingProfile.value = true;
  try {
    applyProfile(await fetchStoryProfile(book.book_id));
  } catch {
    ElMessage.error("故事设定加载失败");
  } finally {
    loadingProfile.value = false;
  }
}

async function runStoryProfileGeneration() {
  if (!profileBook.value) {
    return;
  }
  generatingProfile.value = true;
  try {
    applyProfile(await generateStoryProfile(profileBook.value.book_id));
    ElMessage.success("故事设定已生成");
  } catch {
    ElMessage.error("故事设定生成失败");
  } finally {
    generatingProfile.value = false;
  }
}

async function saveStoryProfile() {
  if (!profileBook.value) {
    return;
  }
  savingProfile.value = true;
  try {
    const payload = {
      title: profileForm.title,
      genre: profileForm.genre,
      overview: profileForm.overview,
      world_setting: profileForm.world_setting,
      main_conflict: profileForm.main_conflict,
      tone: profileForm.tone,
      confirmed: profileForm.confirmed,
      characters: parseJsonArray(profileJson.characters, "人物"),
      key_events: parseJsonArray(profileJson.key_events, "关键事件"),
      clues: parseJsonArray(profileJson.clues, "线索")
    };
    applyProfile(await updateStoryProfile(profileBook.value.book_id, payload));
    ElMessage.success("故事设定已保存");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "故事设定保存失败");
  } finally {
    savingProfile.value = false;
  }
}

onMounted(loadBooks);
</script>
