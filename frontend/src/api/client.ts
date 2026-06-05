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
