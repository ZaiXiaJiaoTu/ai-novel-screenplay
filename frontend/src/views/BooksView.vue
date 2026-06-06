<template>
  <section class="books-page">
    <div class="page-header books-header">
      <div>
        <h1 class="page-title">小说书架</h1>
        <p class="page-subtitle">上传小说后自动切分章节，在右侧维护章节标题和正文。</p>
      </div>
      <el-button :icon="Refresh" :loading="loadingBooks" @click="loadBooks">刷新</el-button>
    </div>

    <div class="bookshelf-layout">
      <aside class="bookshelf-sidebar">
        <div class="bookshelf-sidebar-header">
          <div>
            <div class="panel-title">作品列表</div>
            <p class="page-subtitle">共 {{ books.length }} 部作品</p>
          </div>
          <el-button type="primary" :icon="Upload" @click="openUploadDialog">
            上传作品
          </el-button>
        </div>

        <el-scrollbar class="book-list-scroll" v-loading="loadingBooks">
          <button
            v-for="book in books"
            :key="book.book_id"
            class="book-list-item"
            :class="{ active: selectedBook?.book_id === book.book_id }"
            type="button"
            @click="selectBook(book)"
          >
            <span class="book-title">{{ book.title }}</span>
            <span class="book-meta">
              {{ formatNovelType(book.novel_type) }} / {{ book.chapter_count }} 章 /
              {{ book.word_count }} 字
            </span>
          </button>
          <el-empty v-if="!loadingBooks && books.length === 0" description="暂无作品" />
        </el-scrollbar>
      </aside>

      <main class="chapter-workspace">
        <div class="chapter-toolbar">
          <div>
            <div class="panel-title">
              {{ selectedBook ? selectedBook.title : "章节切分" }}
            </div>
            <p class="page-subtitle">
              {{
                selectedBook
                  ? `${chapters.length} 个章节，可编辑标题与正文`
                  : "请选择左侧作品查看章节"
              }}
            </p>
          </div>
          <el-button
            type="primary"
            :icon="Plus"
            :disabled="!selectedBook"
            @click="openCreateChapterDialog"
          >
            增加章节
          </el-button>
        </div>

        <el-table
          v-loading="loadingChapters"
          :data="chapters"
          empty-text="暂无章节"
          height="calc(100vh - 260px)"
        >
          <el-table-column prop="chapter_index" label="序号" width="80" />
          <el-table-column prop="title" label="章节标题" min-width="260" show-overflow-tooltip />
          <el-table-column prop="word_count" label="字数" width="110" />
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :icon="Edit" @click="openEditChapterDialog(row)">
                编辑
              </el-button>
              <el-button link type="danger" :icon="Delete" @click="removeChapter(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </main>
    </div>

    <el-dialog v-model="uploadVisible" title="上传作品" width="680px" destroy-on-close>
      <el-tabs v-model="activeUploadTab">
        <el-tab-pane label="文本输入" name="text">
          <el-form label-position="top">
            <el-form-item label="作品名称">
              <el-input v-model="textForm.title" maxlength="80" show-word-limit />
            </el-form-item>
            <el-form-item label="小说正文">
              <el-input
                v-model="textForm.content"
                type="textarea"
                :rows="12"
                placeholder="粘贴包含章节标题的小说正文"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="文件上传" name="file">
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
              ref="uploadRef"
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
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingBook" @click="submitBook">
          上传作品
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="chapterDialogVisible"
      :title="editingChapter ? '编辑章节' : '新增章节'"
      width="760px"
      destroy-on-close
    >
      <el-form label-position="top">
        <div class="chapter-form-grid">
          <el-form-item label="章节标题">
            <el-input v-model="chapterForm.title" maxlength="120" show-word-limit />
          </el-form-item>
          <el-form-item v-if="!editingChapter" label="插入位置">
            <el-input-number
              v-model="chapterForm.chapter_index"
              :min="1"
              :max="chapters.length + 1"
            />
          </el-form-item>
        </div>
        <el-form-item label="章节正文">
          <el-input v-model="chapterForm.content" type="textarea" :rows="16" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chapterDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingChapter" @click="saveChapter">
          保存
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { Delete, Edit, Plus, Refresh, Upload, UploadFilled } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox, type UploadFile, type UploadInstance } from "element-plus";
import { onMounted, reactive, ref } from "vue";

import {
  type BookListItem,
  type ChapterDetail,
  type ChapterListItem,
  createBookFromText,
  createChapter,
  deleteChapter,
  fetchBookChapters,
  fetchBooks,
  fetchChapter,
  updateChapter,
  uploadBook
} from "@/api/client";

const books = ref<BookListItem[]>([]);
const chapters = ref<ChapterListItem[]>([]);
const selectedBook = ref<BookListItem | null>(null);
const selectedFile = ref<File | null>(null);
const uploadRef = ref<UploadInstance>();
const loadingBooks = ref(false);
const loadingChapters = ref(false);
const creatingBook = ref(false);
const savingChapter = ref(false);
const uploadVisible = ref(false);
const chapterDialogVisible = ref(false);
const activeUploadTab = ref("text");
const editingChapter = ref<ChapterDetail | null>(null);
const fileTitle = ref("");
const textForm = reactive({
  title: "",
  content: ""
});
const chapterForm = reactive({
  title: "",
  content: "",
  chapter_index: 1
});

function formatNovelType(type: string | null) {
  const labels: Record<string, string> = {
    short: "短篇",
    middle: "中篇",
    long: "长篇"
  };
  return type ? labels[type] || type : "未分类";
}

function openUploadDialog() {
  uploadVisible.value = true;
}

async function loadBooks() {
  loadingBooks.value = true;
  try {
    const result = await fetchBooks();
    books.value = result.records;
    if (!selectedBook.value && books.value.length > 0) {
      await selectBook(books.value[0]);
    } else if (
      selectedBook.value &&
      !books.value.some((book) => book.book_id === selectedBook.value?.book_id)
    ) {
      selectedBook.value = null;
      chapters.value = [];
    }
  } catch {
    books.value = [];
    ElMessage.error("作品列表加载失败，请检查后端服务和数据库连接");
  } finally {
    loadingBooks.value = false;
  }
}

async function loadChapters(bookId: number) {
  loadingChapters.value = true;
  try {
    chapters.value = await fetchBookChapters(bookId);
  } catch {
    chapters.value = [];
    ElMessage.error("章节列表加载失败");
  } finally {
    loadingChapters.value = false;
  }
}

async function selectBook(book: BookListItem) {
  selectedBook.value = book;
  await loadChapters(book.book_id);
}

function selectFile(uploadFile: UploadFile) {
  selectedFile.value = uploadFile.raw ?? null;
}

function clearFile() {
  selectedFile.value = null;
}

function resetUploadForm() {
  textForm.title = "";
  textForm.content = "";
  fileTitle.value = "";
  selectedFile.value = null;
  uploadRef.value?.clearFiles();
}

async function submitBook() {
  creatingBook.value = true;
  try {
    const result =
      activeUploadTab.value === "text"
        ? await submitTextBook()
        : await submitFileBook();
    if (!result) {
      return;
    }
    ElMessage.success("上传成功");
    uploadVisible.value = false;
    resetUploadForm();
    await loadBooks();
    const created = books.value.find((item) => item.book_id === result.book_id);
    if (created) {
      await selectBook(created);
    }
  } finally {
    creatingBook.value = false;
  }
}

async function submitTextBook() {
  if (!textForm.title.trim() || !textForm.content.trim()) {
    ElMessage.warning("请填写作品名称和小说正文");
    return null;
  }
  try {
    return await createBookFromText({
      title: textForm.title.trim(),
      content: textForm.content
    });
  } catch {
    ElMessage.error("文本上传失败");
    return null;
  }
}

async function submitFileBook() {
  if (!selectedFile.value) {
    ElMessage.warning("请选择 txt 文件");
    return null;
  }
  try {
    return await uploadBook(selectedFile.value, fileTitle.value);
  } catch {
    ElMessage.error("文件上传失败");
    return null;
  }
}

function openCreateChapterDialog() {
  if (!selectedBook.value) {
    return;
  }
  editingChapter.value = null;
  chapterForm.title = "";
  chapterForm.content = "";
  chapterForm.chapter_index = chapters.value.length + 1;
  chapterDialogVisible.value = true;
}

async function openEditChapterDialog(chapter: ChapterListItem) {
  try {
    const detail = await fetchChapter(chapter.chapter_id);
    editingChapter.value = detail;
    chapterForm.title = detail.title;
    chapterForm.content = detail.content;
    chapterForm.chapter_index = detail.chapter_index;
    chapterDialogVisible.value = true;
  } catch {
    ElMessage.error("章节内容加载失败");
  }
}

async function saveChapter() {
  if (!selectedBook.value) {
    return;
  }
  if (!chapterForm.title.trim() || !chapterForm.content.trim()) {
    ElMessage.warning("请填写章节标题和正文");
    return;
  }
  savingChapter.value = true;
  try {
    if (editingChapter.value) {
      await updateChapter(editingChapter.value.chapter_id, {
        title: chapterForm.title.trim(),
        content: chapterForm.content
      });
      ElMessage.success("章节已保存");
    } else {
      await createChapter(selectedBook.value.book_id, {
        title: chapterForm.title.trim(),
        content: chapterForm.content,
        chapter_index: chapterForm.chapter_index
      });
      ElMessage.success("章节已新增");
    }
    chapterDialogVisible.value = false;
    await loadChapters(selectedBook.value.book_id);
    await loadBooks();
  } catch {
    ElMessage.error("章节保存失败");
  } finally {
    savingChapter.value = false;
  }
}

async function removeChapter(chapter: ChapterListItem) {
  if (!selectedBook.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除「${chapter.title}」吗？`, "删除章节", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消"
    });
  } catch {
    return;
  }

  try {
    await deleteChapter(chapter.chapter_id);
    ElMessage.success("章节已删除");
    await loadChapters(selectedBook.value.book_id);
    await loadBooks();
  } catch {
    ElMessage.error("章节删除失败");
  }
}

onMounted(loadBooks);
</script>
