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

export interface ChapterDetail extends ChapterListItem {
  book_id: number;
  content: string;
}

export interface ChapterPayload {
  title: string;
  content: string;
  chapter_index?: number;
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

export interface LlmCallLogListItem {
  log_id: number;
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

export type AdaptationType = "tv" | "short_drama" | "animation" | "audio_drama";
export type PacingLevel = "fast" | "medium" | "slow";
export type DensityLevel = "high" | "medium" | "low";

export interface ScriptAdaptationProject {
  project_id: number;
  book_id: number;
  book_title: string;
  project_name: string;
  adaptation_type: AdaptationType;
  episode_duration: number | null;
  pacing: PacingLevel;
  scene_frequency: DensityLevel;
  dialogue_density: DensityLevel;
  events_per_episode: number;
  yaml_schema_delta: Record<string, unknown> | null;
  split_status: string;
  split_stop_requested: boolean;
  generation_status: string;
  generation_stop_requested: boolean;
  event_count: number;
  character_count: number;
  episode_count: number;
}

export interface ScriptAdaptationProjectList {
  records: ScriptAdaptationProject[];
  total: number;
}

export interface ScriptAdaptationCreatePayload {
  book_id: number;
  project_name: string;
  adaptation_type: AdaptationType;
  episode_duration: number;
  pacing: PacingLevel;
  scene_frequency: DensityLevel;
  dialogue_density: DensityLevel;
  events_per_episode: number;
}

export type ScriptAdaptationConfigPayload = Partial<
  Omit<ScriptAdaptationCreatePayload, "book_id" | "adaptation_type">
>;

export interface ScriptWorkflowProgress {
  project_id: number;
  chapter_count: number;
  split_chapter_count: number;
  batch_count: number;
  event_count: number;
  locked_event_count: number;
  episode_count: number;
  split_status: string;
  split_stop_requested: boolean;
  generation_status: string;
  generation_stop_requested: boolean;
}

export interface ScriptEventBatchDetail {
  batch_id: number;
  batch_index: number;
  chapter_start_index: number;
  chapter_end_index: number;
  status: string;
  event_count: number;
}

export interface ScriptPlotEventDetail {
  event_id: number;
  batch_id: number;
  event_index: number;
  content: string;
  source_chapter_start: number;
  source_chapter_end: number;
  locked: boolean;
}

export interface ScriptCharacterDetail {
  character_id: number;
  name: string;
  profile: string;
  metadata_json: Record<string, unknown> | null;
}

export interface ScriptEpisodeDetail {
  episode_id: number;
  episode_index: number;
  title: string;
  event_ids: number[];
  yaml_content: string | null;
  yaml_payload: Record<string, unknown> | null;
  plain_text_content: string | null;
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

export async function deleteBook(bookId: number) {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ book_id: number; deleted: boolean }>>(`/books/${bookId}`)
  );
}

export async function fetchBookChapters(bookId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ChapterListItem[]>>(`/books/${bookId}/chapters`)
  );
}

export async function fetchChapter(chapterId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ChapterDetail>>(`/chapters/${chapterId}`)
  );
}

export async function createChapter(bookId: number, payload: ChapterPayload) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ChapterDetail>>(`/books/${bookId}/chapters`, payload)
  );
}

export async function updateChapter(
  chapterId: number,
  payload: Partial<Omit<ChapterPayload, "chapter_index">>
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<ChapterDetail>>(`/chapters/${chapterId}`, payload)
  );
}

export async function deleteChapter(chapterId: number) {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ chapter_id: number; deleted: boolean }>>(
      `/chapters/${chapterId}`
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

export async function clearLlmCallLogs() {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ deleted_count: number }>>("/llm-call-logs")
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

export async function fetchScriptAdaptations(params?: { page?: number; size?: number }) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptAdaptationProjectList>>("/script-adaptations", {
      params
    })
  );
}

export async function createScriptAdaptation(payload: ScriptAdaptationCreatePayload) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptAdaptationProject>>("/script-adaptations", payload)
  );
}

export async function updateScriptAdaptationConfig(
  projectId: number,
  payload: ScriptAdaptationConfigPayload
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<ScriptAdaptationProject>>(
      `/script-adaptations/${projectId}/config`,
      payload
    )
  );
}

export async function deleteScriptAdaptation(projectId: number) {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ deleted: boolean }>>(`/script-adaptations/${projectId}`)
  );
}

export async function fetchScriptAdaptationProgress(projectId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptWorkflowProgress>>(
      `/script-adaptations/${projectId}/progress`
    )
  );
}

export async function splitScriptEventsOnce(projectId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptWorkflowProgress>>(
      `/script-adaptations/${projectId}/split/once`,
      undefined,
      { timeout: 180000 }
    )
  );
}

export async function splitScriptEventsAll(projectId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptWorkflowProgress>>(
      `/script-adaptations/${projectId}/split/all`,
      undefined,
      { timeout: 30000 }
    )
  );
}

export async function stopScriptEventSplit(projectId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptWorkflowProgress>>(
      `/script-adaptations/${projectId}/split/stop`
    )
  );
}

export async function fetchScriptEventBatches(projectId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptEventBatchDetail[]>>(
      `/script-adaptations/${projectId}/batches`
    )
  );
}

export async function fetchScriptPlotEvents(projectId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptPlotEventDetail[]>>(
      `/script-adaptations/${projectId}/events`
    )
  );
}

export async function updateScriptPlotEvent(eventId: number, payload: { content: string }) {
  return unwrap(
    await apiClient.put<ApiEnvelope<ScriptPlotEventDetail>>(
      `/script-adaptations/events/${eventId}`,
      payload
    )
  );
}

export async function deleteScriptPlotEvent(eventId: number) {
  return unwrap(
    await apiClient.delete<ApiEnvelope<{ deleted: boolean }>>(
      `/script-adaptations/events/${eventId}`
    )
  );
}

export async function fetchScriptCharacters(projectId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptCharacterDetail[]>>(
      `/script-adaptations/${projectId}/characters`
    )
  );
}

export async function consolidateScriptCharacters(projectId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptCharacterDetail[]>>(
      `/script-adaptations/${projectId}/characters/consolidate`,
      undefined,
      { timeout: 180000 }
    )
  );
}

export async function updateScriptCharacter(
  characterId: number,
  payload: { name?: string; profile?: string; metadata_json?: Record<string, unknown> | null }
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<ScriptCharacterDetail>>(
      `/script-adaptations/characters/${characterId}`,
      payload
    )
  );
}

export async function generateScriptEpisodeOnce(
  projectId: number,
  payload: { events_per_episode?: number }
) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptEpisodeDetail>>(
      `/script-adaptations/${projectId}/episodes/once`,
      payload,
      { timeout: 180000 }
    )
  );
}

export async function generateScriptEpisodesAll(
  projectId: number,
  payload: { events_per_episode?: number }
) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptWorkflowProgress>>(
      `/script-adaptations/${projectId}/episodes/all`,
      payload,
      { timeout: 30000 }
    )
  );
}

export async function stopScriptEpisodeGeneration(projectId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptWorkflowProgress>>(
      `/script-adaptations/${projectId}/episodes/stop`
    )
  );
}

export async function fetchScriptEpisodes(projectId: number) {
  return unwrap(
    await apiClient.get<ApiEnvelope<ScriptEpisodeDetail[]>>(
      `/script-adaptations/${projectId}/episodes`
    )
  );
}

export async function updateScriptEpisode(
  episodeId: number,
  payload: {
    title?: string;
    yaml_content?: string | null;
    yaml_payload?: Record<string, unknown> | null;
    plain_text_content?: string | null;
  }
) {
  return unwrap(
    await apiClient.put<ApiEnvelope<ScriptEpisodeDetail>>(
      `/script-adaptations/episodes/${episodeId}`,
      payload
    )
  );
}

export async function repairScriptEpisode(episodeId: number) {
  return unwrap(
    await apiClient.post<ApiEnvelope<ScriptEpisodeDetail>>(
      `/script-adaptations/episodes/${episodeId}/repair`,
      undefined,
      { timeout: 180000 }
    )
  );
}

export function scriptAdaptationEpisodeDownloadUrl(episodeId: number, format: "yaml" | "txt") {
  return `/api/script-adaptations/episodes/${episodeId}/download?format=${format}`;
}

export function scriptAdaptationDownloadUrl(projectId: number, format: "yaml" | "txt") {
  return `/api/script-adaptations/${projectId}/download?format=${format}`;
}
