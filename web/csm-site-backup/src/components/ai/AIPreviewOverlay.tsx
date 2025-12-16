import React from 'react';
import { Shield, AlertCircle } from 'lucide-react';

interface AIPreviewOverlayProps {
  isVisible: boolean;
  onClose: () => void;
}

export function AIPreviewOverlay({ isVisible, onClose }: AIPreviewOverlayProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative max-w-2xl w-full mx-4 bg-black/90 rounded-xl border border-white/10 p-8">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
          aria-label="Close preview"
        >
          <AlertCircle className="w-6 h-6" />
        </button>

        <div className="flex items-center justify-center mb-6">
          <Shield className="w-12 h-12 text-white/80" />
        </div>

        <h2 className="text-2xl font-bold text-center mb-4">
          AI Demo Preview Mode
        </h2>

        <p className="text-gray-300 text-center mb-6">
          This is a demonstration view of our AI capabilities. For full interactive access
          and custom AI solutions, please contact us directly.
        </p>

        <div className="flex justify-center gap-4">
          <a
            href="mailto:complexsimplicitymedia@gmail.com?subject=AI%20Solutions%20Inquiry"
            className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
          >
            Contact Us
          </a>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}