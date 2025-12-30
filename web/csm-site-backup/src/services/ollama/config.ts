export const OLLAMA_CONFIG = {
  baseUrl: 'http://localhost:11434',
  defaultModel: 'llama2',
  timeout: 30000,
  retries: 3,
  models: {
    llama2: {
      name: 'llama2',
      parameters: {
        temperature: 0.7,
        top_k: 40,
        top_p: 0.9,
        repeat_penalty: 1.1,
        num_ctx: 4096
      }
    },
    codellama: {
      name: 'codellama',
      parameters: {
        temperature: 0.8,
        top_k: 50,
        top_p: 0.95,
        repeat_penalty: 1.1,
        num_ctx: 4096
      }
    },
    mistral: {
      name: 'mistral',
      parameters: {
        temperature: 0.7,
        top_k: 40,
        top_p: 0.9,
        repeat_penalty: 1.1,
        num_ctx: 8192
      }
    }
  }
};