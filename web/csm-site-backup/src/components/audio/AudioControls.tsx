import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useAudioContext } from '../../contexts/AudioContext';

export function AudioControls() {
  const { isMuted, toggleMute, volume, setVolume } = useAudioContext();

  return (
    <div className="fixed top-8 right-8 z-50 flex items-center gap-4 bg-black/30 backdrop-blur-md rounded-full px-4 py-2 border border-white/10">
      <button
        onClick={toggleMute}
        className="text-white/70 hover:text-white transition-colors duration-300"
        aria-label={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
      </button>
      <input
        type="range"
        min="0"
        max="1"
        step="0.1"
        value={volume}
        onChange={(e) => setVolume(parseFloat(e.target.value))}
        className="w-24 h-1 bg-white/20 rounded-full appearance-none cursor-pointer"
        style={{
          backgroundImage: `linear-gradient(to right, white ${volume * 100}%, transparent ${volume * 100}%)`,
        }}
      />
    </div>
  );
}