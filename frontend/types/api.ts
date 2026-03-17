export interface HealthStatus {
  app_ready?: boolean;
  status?: string;
  sqlite_ready?: boolean;
  dify_configured?: boolean;
  dify_reachable?: boolean;
  graph_enabled?: boolean;
  graph_loaded?: boolean;
  graph_node_count?: number;
  graph_edge_count?: number;
  graph_instance_id?: string;
  graph_db_version?: string | null;
  graph_instance_local_path_exists?: boolean;
  csv_export_ready?: boolean;
  admin_auth_ready?: boolean;
  document_module_ready?: boolean;
  current_mode?: string;
  app_env?: string;
  service?: string;
  dify_validation_warnings?: string[];
}

export interface DifyDebugRequest {
  base_url: string;
  api_key: string;
  timeout_seconds?: number;
  workflow_id?: string | null;
  response_mode?: string;
  text_input_variable?: string | null;
  file_input_variable?: string | null;
  enable_trace?: boolean;
  user_prefix?: string;
  sample_text?: string | null;
}

export interface DifyDebugResponse {
  reachable: boolean;
  validation_ok: boolean;
  config_summary: Record<string, unknown>;
  parameters?: Record<string, unknown> | null;
  info?: Record<string, unknown> | null;
  workflow_result?: Record<string, unknown> | null;
  warnings: string[];
  logs_saved_to: string;
}

export interface DifyDebugLogRecord {
  recorded_at: string;
  event: string;
  status: string;
  payload: Record<string, unknown>;
}

export interface DifyDebugLogListResponse {
  items: DifyDebugLogRecord[];
}

export interface RootInfo {
  service: string;
  status: string;
  health_url: string;
  exports_api: {
    trigger_qa_logs: string;
    list: string;
  };
  latest_export: ExportRecord | null;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AdminMe {
  admin_id: string;
  username: string;
  roles: string[];
}

export interface ChatResponse {
  message_id: string;
  session_id: string;
  answer: string;
  source: string;
  sources: string[];
  retrieved_context?: string | null;
  status: string;
  provider_message_id?: string | null;
  workflow_run_id?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface FeedbackResponse {
  id: string;
  qa_log_id: string;
  rating: number | null;
  liked: boolean | null;
  comment: string | null;
  source: string;
  created_at: string;
}

export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, unknown>;
  detail?: Record<string, unknown> | null;
}

export interface GraphEdge {
  id: string;
  type: string;
  source: string;
  target: string;
  properties: Record<string, unknown>;
}

export interface GraphOverview {
  nodes: GraphNode[];
  edges: GraphEdge[];
  center?: GraphNode | null;
  detail?: GraphNode | null;
  metadata?: Record<string, unknown>;
  total_nodes: number;
  total_edges: number;
}

export interface GraphNodeDetails {
  node: GraphNode;
  detail?: GraphNode | null;
  description?: string | null;
  source_documents?: GraphSourceDocument[];
  related_entities?: RelatedGraphEntity[];
  metadata?: Record<string, unknown>;
}

export interface GraphSourceDocument {
  document_id?: string | null;
  title: string;
}

export interface RelatedGraphEntity {
  id: string;
  name: string;
  node_type?: string | null;
  labels: string[];
}

export interface GraphNeighbors {
  center_node_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  center?: GraphNode | null;
  detail?: GraphNode | null;
  metadata?: Record<string, unknown>;
}

export interface GraphSummary {
  loaded: boolean;
  node_count: number;
  edge_count: number;
  current_version: string | null;
  sqlite_path: string;
  last_loaded_at: string | null;
}

export interface GraphAdminStatus extends GraphSummary {
  enabled: boolean;
  instance_id: string;
  graph_db_version: string | null;
  import_dir: string;
  export_dir: string;
  import_dir_exists: boolean;
  export_dir_exists: boolean;
  instance_local_path: string;
  instance_local_path_exists: boolean;
  multi_instance_mode: string;
}

export interface GraphFileOperation {
  record_id: string;
  filename: string;
  file_path: string;
  download_url: string | null;
  version: string | null;
  loaded: boolean;
  node_count: number;
  edge_count: number;
  current_version: string | null;
  sqlite_path: string;
  last_loaded_at: string | null;
}

export interface GraphReload {
  loaded: boolean;
  node_count: number;
  edge_count: number;
  current_version: string | null;
  sqlite_path: string;
  last_loaded_at: string | null;
}

export interface DocumentRecord {
  id: string;
  filename: string;
  file_type?: string | null;
  status: string;
  source_type: string;
  uploaded_at: string;
  synced_to_dify: boolean;
  synced_to_graph: boolean;
  note: string | null;
  local_path: string | null;
  source_uri: string | null;
  mime_type: string | null;
  content_type: string | null;
  file_size: number | null;
  file_extension: string | null;
  dify_upload_file_id: string | null;
  dify_uploaded_at: string | null;
  dify_sync_status: string | null;
  dify_error_code: string | null;
  dify_error_message: string | null;
  created_by: string | null;
  created_at: string;
  last_sync_target: string | null;
  last_sync_status: string | null;
  last_sync_at: string | null;
  removed_from_graph_at?: string | null;
  invalidated_at?: string | null;
  is_active?: boolean;
  extraction_task_id?: string | null;
  dify_file_input_variable: string | null;
  dify_workflow_file_input: Record<string, unknown> | null;
}

export interface DocumentListResponse {
  items: DocumentRecord[];
}

export interface SyncResponse {
  document_id: string;
  status: string;
  target_system: string;
  message: string;
}

export interface GraphManagedFile {
  id: string;
  filename: string;
  file_type: string;
  source_type: string;
  status: string;
  uploaded_at: string;
  synced_to_dify: boolean;
  synced_to_graph: boolean;
  note: string | null;
  local_path: string | null;
  source_uri: string | null;
  mime_type: string | null;
  content_type: string | null;
  file_size: number | null;
  file_extension: string | null;
  created_by: string | null;
  created_at: string;
  last_sync_target: string | null;
  last_sync_status: string | null;
  last_sync_at: string | null;
  removed_from_graph_at: string | null;
  invalidated_at: string | null;
  is_active: boolean;
  extraction_task_id: string | null;
}

export interface GraphManagedFileListResponse {
  items: GraphManagedFile[];
}

export interface ExtractionTask {
  id: string;
  task_type: string | null;
  status: string;
  selected_document_ids: string[] | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  result_summary: string | null;
  output_graph_version: string | null;
  operator: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ExtractionTaskListResponse {
  items: ExtractionTask[];
}

export interface GraphPromptSetting {
  prompt_text: string;
  updated_at: string | null;
  updated_by: string | null;
  is_active: boolean;
}

export interface GraphModelSetting {
  provider: string;
  model_name: string;
  api_base_url: string | null;
  enabled: boolean;
  thinking_enabled: boolean;
  is_active: boolean;
  updated_at: string | null;
  updated_by: string | null;
  has_api_key: boolean;
}

export interface ReviewRubric {
  rubric_text: string;
  updated_at: string | null;
  updated_by: string | null;
  is_active: boolean;
}

export interface ReviewEvaluationResponse {
  score: number;
  reason: string;
  rubric_updated_at: string | null;
}

export interface ExportRecord {
  export_id: string;
  export_type: string;
  export_time: string;
  record_count: number;
  operator: string;
  filename: string;
  download_url: string;
  success?: boolean;
}

export interface ExportListResponse {
  items: ExportRecord[];
}

export interface LogFeedbackSummary {
  id: string;
  rating: number | null;
  liked: boolean | null;
  comment: string | null;
  source: string;
  created_at: string;
}

export interface AdminLogRecord {
  id: string;
  question: string;
  retrieved_context: string | null;
  answer: string;
  created_at: string;
  session_id: string | null;
  source: string;
  feedback: LogFeedbackSummary | null;
}

export interface AdminLogListResponse {
  items: AdminLogRecord[];
}
