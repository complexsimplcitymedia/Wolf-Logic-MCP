import React, { useEffect, useState, useCallback, useMemo } from 'react';

interface Star {
  id: string;
  size: 'small' | 'medium' | 'large';
  style: React.CSSProperties;
}

export function StarField() {
  const stars = useMemo(() => {
    const starCount = {
      small: 400,
      medium: 100,
      large: 50
    };

    return Object.entries(starCount).flatMap(([size, count]) =>
      Array.from({ length: count }, (_, i) => ({
        id: `star-${size}-${i}`,
        size: size as 'small' | 'medium' | 'large',
        style: {
          top: `${Math.random() * 100}%`,
          left: `${Math.random() * 100}%`,
          animationDelay: `${Math.random() * 3}s`,
        }
      }))
    );
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {stars.map((star) => (
        <div
          key={star.id}
          className={`absolute rounded-full bg-white animate-twinkle
            ${star.size === 'small' ? 'w-px h-px' : ''}
            ${star.size === 'medium' ? 'w-1 h-1' : ''}
            ${star.size === 'large' ? 'w-1.5 h-1.5' : ''}`}
          style={star.style}
        />
      ))}
    </div>
  );
}