export interface OllamaModelConfig {
  name: string;
  parameters?: {
    temperature?: number;
    top_k?: number;
    top_p?: number;
    repeat_penalty?: number;
    seed?: number;
    stop?: string[];
    num_predict?: number;
    num_ctx?: number;
  };
}

export interface OllamaResponse {
  model: string;
  created_at: string;
  response: string;
  done: boolean;
  context?: number[];
  total_duration?: number;
  load_duration?: number;
  prompt_eval_duration?: number;
  eval_duration?: number;
  eval_count?: number;
}

export interface OllamaError {
  error: string;
  code?: number;
}