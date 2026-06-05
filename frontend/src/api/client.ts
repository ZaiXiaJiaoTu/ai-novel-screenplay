import axios, { type AxiosResponse } from "axios";

export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000
});

export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data: T;
}

export interface BookListItem {
  book_id: number;
  title: string;
  novel_type: string | null;
  chapter_count: number;
  word_count: number;
  preprocess_status: string;
}

export interface BookListResult {
  records: BookListItem[];
  total: number;
}

export interface BookCreateResult {
  book_id: number;
  title: string;
  preprocess_status: string;
}

export interface ChapterListItem {
  chapter_id: number;
  chapter_index: number;
  title: string;
  word_count: number;
}

export interface ChapterSummaryDetail {
  summary_id: number;
  book_id: number;
  chapter_id: number;
  chapter_index: number;
  chapter_title: string;
  summary: string | null;
  characters: unknown[];
  key_events: unknown[];
  locations: unknown[];
  clues: unknown[];
  emotion_changes: unknown[];
}

export interface ChapterSummaryGenerationResult {
  book_id: number;
  generated_count: number;
  summaries: ChapterSummaryDetail[];
}

export interface LlmConfigDetail {
  config_id: number;
  provider: string;
  base_url: string;
  model_name: string;
  temperature: string | number | null;
  top_p: string | number | null;
  max_tokens: number | null;
  timeout_seconds: number;
  retry_count: number;
  task_scope: string[] | null;
  enabled: boolean;
  api_key_masked: string;
  is_default: boolean;
}

export interface LlmConfigPayload {
  provider: string;
  base_url: string;
  api_key?: string;
  model_name: string;
  temperature?: number | null;
  top_p?: number | null;
  max_tokens?: number | null;
  timeout_seconds: number;
  retry_count: number;
  task_scope?: string[] | null;
  enabled: boolean;
  is_default?: boolean;
}

export interface LlmConfigTestResult {
  provider: string;
  model_name: string;
  latency_ms: number;
  status: string;
}

function unwrap<T>(response: AxiosResponse<ApiEnvelope<T>>): T {
  return response.data.data;
}

export async function fetchBooks() {
  return unwrap(await apiClient.get<ApiEnvelope<BookListResult>>("/books"));
}

export async function createBookFromText(payload: { title: string; content: string }) {
  return unwrap(await apiClient.post<ApiEnvelope<BookCreateResult>>("/books/text", payload));
}

export async function uploadBook(file: File, title?: string) {
  const formData = new FormData();
  formData.append("file", file);
  if (title?.trim()) {
    formData.append("title", title.trim());
  }
  return unwrap(await apiClient.post<ApiEnvelope<BookCreateResult>>("/books/upload", formData));
}

export async function fetchBookChapters(bookId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ChapterListItem[]>>(`/books/${bookId}/chapters`)
  );
}

export async function generateChapterSummaries(bookId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ChapterSummaryGenerationResult>>(
      `/books/${bookId}/chapter-summaries/generate`
    )
  );
}

export async function fetchChapterSummary(chapterId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ChapterSummaryDetail>>(`/chapters/${chapterId}/summary`)
  );
}

export async function fetchLlmConfigs() {
  return unwrap(await apiClient.get<ApiEnvelope<LlmConfigDetail[]>>("/llm-configs"));
}

export async function createLlmConfig(payload: LlmConfigPayload & { api_key: string }) {
  return unwrap(await apiClient.post<ApiEnvelope<LlmConfigDetail>>("/llm-configs", payload));
}

export async function updateLlmConfig(configId: number, payload: Partial<LlmConfigPayload>) {
  return unwrap(
    await apiClient.put<ApiEnvelope<LlmConfigDetail>>(`/llm-configs/${configId}`, payload)
  );
}

export async function deleteLlmConfig(configId: number) {
  return unwrap(await apiClient.delete<ApiEnvelope<{ deleted: boolean }>>(`/llm-configs/${configId}`));
}

export async function setDefaultLlmConfig(configId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<LlmConfigDetail>>(`/llm-configs/${configId}/default`)
  );
}

export async function testLlmConfig(configId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<LlmConfigTestResult>>(`/llm-configs/${configId}/test`)
  );
}
