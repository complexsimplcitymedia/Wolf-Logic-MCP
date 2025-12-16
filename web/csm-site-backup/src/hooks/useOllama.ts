import { useState, useCallback } from 'react';
import { ollamaClient } from '../services/ollama/client';
import type { OllamaModelConfig, OllamaResponse } from '../services/ollama/types';

interface UseOllamaOptions {
  onError?: (error: Error) => void;
  onComplete?: (response: OllamaResponse) => void;
}

export function useOllama(options: UseOllamaOptions = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const generate = useCallback(async (
    prompt: string,
    modelConfig?: OllamaModelConfig
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await ollamaClient.generate(prompt, modelConfig);
      options.onComplete?.(response);
      return response;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error occurred');
      setError(error);
      options.onError?.(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  const streamGenerate = useCallback(async (
    prompt: string,
    onToken: (token: string) => void,
    modelConfig?: OllamaModelConfig
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      await ollamaClient.streamGenerate(prompt, onToken, modelConfig);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error occurred');
      setError(error);
      options.onError?.(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  return {
    generate,
    streamGenerate,
    isLoading,
    error
  };
}