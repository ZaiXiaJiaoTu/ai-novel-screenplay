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

export interface StoryProfileDetail {
  profile_id: number;
  book_id: number;
  title: string | null;
  genre: string | null;
  overview: string | null;
  world_setting: string | null;
  main_conflict: string | null;
  characters: unknown[] | null;
  relationships: unknown[] | null;
  key_events: unknown[] | null;
  chapter_outlines: unknown[] | null;
  clues: unknown[] | null;
  tone: string | null;
  locked_settings: unknown[] | Record<string, unknown> | null;
  confirmed: boolean;
  version: number;
}

export type StoryProfilePayload = Partial<
  Omit<StoryProfileDetail, "profile_id" | "book_id" | "version">
>;

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

export interface LlmCallLogListItem {
  log_id: number;
  task_id: number | null;
  llm_config_id: number | null;
  prompt_template_id: number | null;
  task_type: string;
  status: string;
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  created_at: string;
}

export interface LlmCallLogListResult {
  records: LlmCallLogListItem[];
  total: number;
}

export interface LlmCallLogDetail extends LlmCallLogListItem {
  request_summary: string | null;
  response_summary: string | null;
  error_message: string | null;
}

export interface PromptTemplateDetail {
  template_id: number;
  template_name: string;
  task_type: string;
  system_prompt: string;
  user_prompt_template: string;
  output_format: string;
  variables: string[] | null;
  enabled: boolean;
  version: number;
}

export interface PromptTemplatePayload {
  template_name: string;
  task_type: string;
  system_prompt: string;
  user_prompt_template: string;
  output_format: string;
  variables: string[] | null;
  enabled: boolean;
}

export interface PromptTemplateVersionDetail {
  version_id: number;
  template_id: number;
  version: number;
  system_prompt: string;
  user_prompt_template: string;
  output_format: string;
  variables: string[] | null;
}

export interface ScriptTaskCreatePayload {
  book_id: number;
  project_id?: number | null;
  adapt_scope: Record<string, unknown>;
  generation_config: Record<string, unknown>;
}

export interface ScriptTaskCreateResult {
  task_id: number;
  status: string;
}

export interface ScriptTaskDetail {
  task_id: number;
  status: string;
  current_step: string | null;
  progress: number;
  error_message: string | null;
}

export interface ScriptTaskListItem extends ScriptTaskDetail {
  book_id: number;
  book_title: string;
  script_project_id: number | null;
  created_at: string;
  finished_at: string | null;
}

export interface ScriptTaskListResult {
  records: ScriptTaskListItem[];
  total: number;
}

export interface GenerationArtifactListItem {
  artifact_id: number;
  artifact_type: string;
  version: number;
  editable: boolean;
}

export interface GenerationArtifactDetail extends GenerationArtifactListItem {
  task_id: number;
  content: Record<string, unknown> | unknown[] | null;
}

export interface ScriptProjectListItem {
  project_id: number;
  project_name: string;
  book_title: string;
  script_type: string | null;
  default_style: string | null;
  segment_count: number;
}

export interface ScriptProjectListResult {
  records: ScriptProjectListItem[];
  total: number;
}

export interface ScriptSegmentListItem {
  segment_id: number;
  segment_name: string;
  style: string | null;
  compression_level: string | null;
  target_duration: number | null;
  scene_count: number;
  status: string;
}

export interface ScriptSegmentDetail extends ScriptSegmentListItem {
  project_id: number;
  book_id: number;
  adapt_scope: Record<string, unknown> | null;
  yaml_content: string | null;
  plain_text_content: string | null;
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

export async function fetchStoryProfile(bookId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<StoryProfileDetail>>(`/books/${bookId}/story-profile`)
  );
}

export async function generateStoryProfile(bookId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<StoryProfileDetail>>(
      `/books/${bookId}/story-profile/generate`
    )
  );
}

export async function updateStoryProfile(bookId: number, payload: StoryProfilePayload) {
  return unwrap(
    await apiClient.put<ApiEnvelope<StoryProfileDetail>>(
      `/books/${bookId}/story-profile`,
      payload
    )
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

export async function fetchLlmCallLogs(params?: {
  task_type?: string;
  status?: string;
  start_time?: string;
  end_time?: string;
  page?: number;
  size?: number;
}) {
  return unwrap(
    await apiClient.get<ApiEnvelope<LlmCallLogListResult>>("/llm-call-logs", { params })
  );
}

export async function fetchLlmCallLog(logId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<LlmCallLogDetail>>(`/llm-call-logs/${logId}`)
  );
}

export async function fetchPromptTemplates(params?: {
  task_type?: string;
  enabled?: boolean;
  keyword?: string;
}) {
  return unwrap(
    await apiClient.get<ApiEnvelope<PromptTemplateDetail[]>>("/prompt-templates", { params })
  );
}

export async function seedDefaultPromptTemplates() {
  return unwrap(
    await apiClient.post<ApiEnvelope<PromptTemplateDetail[]>>("/prompt-templates/seed-defaults")
  );
}

export async function createPromptTemplate(payload: PromptTemplatePayload) {
  return unwrap(
    await apiClient.post<ApiEnvelope<PromptTemplateDetail>>("/prompt-templates", payload)
  );
}

export async function updatePromptTemplate(
  templateId: number,
  payload: Partial<PromptTemplatePayload>
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<PromptTemplateDetail>>(
      `/prompt-templates/${templateId}`,
      payload
    )
  );
}

export async function deletePromptTemplate(templateId: number) {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ deleted: boolean }>>(
      `/prompt-templates/${templateId}`
    )
  );
}

export async function fetchPromptTemplateVersions(templateId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<PromptTemplateVersionDetail[]>>(
      `/prompt-templates/${templateId}/versions`
    )
  );
}

export async function rollbackPromptTemplate(templateId: number, versionId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<PromptTemplateDetail>>(
      `/prompt-templates/${templateId}/rollback/${versionId}`
    )
  );
}

export async function createScriptTask(payload: ScriptTaskCreatePayload) {
  return unwrap(await apiClient.post<ApiEnvelope<ScriptTaskCreateResult>>("/script-tasks", payload));
}

export async function startScriptTask(taskId: number) {
  return unwrap(await apiClient.post<ApiEnvelope<ScriptTaskDetail>>(`/script-tasks/${taskId}/start`));
}

export async function fetchScriptTask(taskId: number) {
  return unwrap(await apiClient.get<ApiEnvelope<ScriptTaskDetail>>(`/script-tasks/${taskId}`));
}

export async function fetchScriptTasks(params?: {
  book_id?: number;
  status?: string;
  page?: number;
  size?: number;
}) {
  return unwrap(await apiClient.get<ApiEnvelope<ScriptTaskListResult>>("/script-tasks", { params }));
}

export async function cancelScriptTask(taskId: number) {
  return unwrap(await apiClient.post<ApiEnvelope<ScriptTaskDetail>>(`/script-tasks/${taskId}/cancel`));
}

export async function retryScriptTask(taskId: number) {
  return unwrap(await apiClient.post<ApiEnvelope<ScriptTaskDetail>>(`/script-tasks/${taskId}/retry`));
}

export async function fetchTaskArtifacts(taskId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<GenerationArtifactListItem[]>>(
      `/script-tasks/${taskId}/artifacts`
    )
  );
}

export async function fetchArtifact(artifactId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<GenerationArtifactDetail>>(`/artifacts/${artifactId}`)
  );
}

export async function updateArtifact(
  artifactId: number,
  payload: { content: Record<string, unknown> | unknown[] }
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<GenerationArtifactDetail>>(`/artifacts/${artifactId}`, payload)
  );
}

export async function fetchScriptProjects(params?: {
  keyword?: string;
  script_type?: string;
  page?: number;
  size?: number;
}) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptProjectListResult>>("/script-projects", { params })
  );
}

export async function fetchScriptSegments(projectId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptSegmentListItem[]>>(
      `/script-projects/${projectId}/segments`
    )
  );
}

export async function fetchScriptSegment(segmentId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptSegmentDetail>>(`/script-segments/${segmentId}`)
  );
}

export async function updateScriptSegmentContent(
  segmentId: number,
  payload: { yaml_content?: string | null; plain_text_content?: string | null }
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<ScriptSegmentDetail>>(
      `/script-segments/${segmentId}/content`,
      payload
    )
  );
}

export async function deleteScriptSegment(segmentId: number) {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ deleted: boolean }>>(`/script-segments/${segmentId}`)
  );
}

export function scriptSegmentDownloadUrl(segmentId: number, format: "yaml" | "txt") {
  return `/api/script-segments/${segmentId}/download?format=${format}`;
}

export function scriptProjectDownloadUrl(projectId: number, format: "yaml" | "txt") {
  return `/api/script-projects/${projectId}/download?format=${format}`;
}
