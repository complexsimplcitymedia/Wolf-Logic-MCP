import React, { createContext, useState, useEffect, useCallback } from 'react';

interface AudioContextType {
  isMuted: boolean;
  toggleMute: () => void;
  setIsMuted: (muted: boolean) => void;
  volume: number;
  setVolume: (volume: number) => void;
  currentVideoId: string | null;
  setCurrentVideoId: (videoId: string | null) => void;
}

const defaultContext: AudioContextType = {
  isMuted: true,
  toggleMute: () => {},
  setIsMuted: () => {},
  volume: 0.5,
  setVolume: () => {},
  currentVideoId: null,
  setCurrentVideoId: () => {}
};

export const AudioContext = createContext<AudioContextType>(defaultContext);

export function AudioProvider({ children }: { children: React.ReactNode }) {
  const [isMuted, setIsMuted] = useState(true);
  const [volume, setVolume] = useState(0.5);
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);

  // Handle user interaction to enable audio
  useEffect(() => {
    const handleUserInteraction = () => {
      if (isMuted) {
        setIsMuted(false);
      }
      // Remove event listeners after first interaction
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
    };

    document.addEventListener('click', handleUserInteraction);
    document.addEventListener('touchstart', handleUserInteraction);

    return () => {
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
    };
  }, [isMuted]);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
  }, []);

  const contextValue = {
    isMuted,
    toggleMute,
    setIsMuted,
    volume,
    setVolume,
    currentVideoId,
    setCurrentVideoId
  };

  return (
    <AudioContext.Provider value={contextValue}>
      {children}
    </AudioContext.Provider>
  );
}