import { OLLAMA_CONFIG } from './config';
import type { OllamaModelConfig, OllamaResponse, OllamaError } from './types';

export class OllamaClient {
  private baseUrl: string;
  private defaultModel: string;
  private timeout: number;
  private retries: number;

  constructor(config = OLLAMA_CONFIG) {
    this.baseUrl = config.baseUrl;
    this.defaultModel = config.defaultModel;
    this.timeout = config.timeout;
    this.retries = config.retries;
  }

  private async fetchWithRetry(url: string, options: RequestInit, retries = this.retries): Promise<Response> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.fetchWithRetry(url, options, retries - 1);
      }
      throw error;
    }
  }

  async generate(prompt: string, modelConfig?: OllamaModelConfig): Promise<OllamaResponse> {
    const model = modelConfig?.name || this.defaultModel;
    const parameters = modelConfig?.parameters || OLLAMA_CONFIG.models[model]?.parameters;

    try {
      const response = await this.fetchWithRetry(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          prompt,
          ...parameters,
          stream: false
        })
      });

      if (!response.ok) {
        const error = await response.json() as OllamaError;
        throw new Error(error.error || 'Failed to generate response');
      }

      return await response.json() as OllamaResponse;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Ollama generation failed: ${error.message}`);
      }
      throw new Error('Unknown error occurred during Ollama generation');
    }
  }

  async streamGenerate(
    prompt: string,
    onToken: (token: string) => void,
    modelConfig?: OllamaModelConfig
  ): Promise<void> {
    const model = modelConfig?.name || this.defaultModel;
    const parameters = modelConfig?.parameters || OLLAMA_CONFIG.models[model]?.parameters;

    try {
      const response = await this.fetchWithRetry(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          prompt,
          ...parameters,
          stream: true
        })
      });

      if (!response.ok) {
        const error = await response.json() as OllamaError;
        throw new Error(error.error || 'Failed to generate response');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Response body is not readable');

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(Boolean);
        
        for (const line of lines) {
          const data = JSON.parse(line) as OllamaResponse;
          onToken(data.response);
          if (data.done) break;
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Ollama stream generation failed: ${error.message}`);
      }
      throw new Error('Unknown error occurred during Ollama stream generation');
    }
  }
}

export const ollamaClient = new OllamaClient();