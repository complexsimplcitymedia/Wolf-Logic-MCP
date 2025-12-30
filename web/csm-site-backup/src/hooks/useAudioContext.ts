import { useState, useCallback } from 'react';

interface UseAudioReturn {
  isMuted: boolean;
  toggleMute: () => void;
  setIsMuted: (muted: boolean) => void;
  volume: number;
  setVolume: (volume: number) => void;
  currentVideoId: string | null;
  setCurrentVideoId: (videoId: string | null) => void;
}

export function useAudioContext(): UseAudioReturn {
  const [isMuted, setIsMuted] = useState(true);
  const [volume, setVolume] = useState(0.5);
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
  }, []);

  return {
    isMuted,
    toggleMute,
    setIsMuted,
    volume,
    setVolume,
    currentVideoId,
    setCurrentVideoId
  };
}