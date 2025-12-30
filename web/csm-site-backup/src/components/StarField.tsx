import React, { useEffect, useState, useCallback, useMemo } from 'react';

interface Star {
  id: string;
  size: 'small' | 'medium' | 'large';
  style: React.CSSProperties;
}

interface ShootingStar {
  id: string;
  style: React.CSSProperties;
}

export function StarField() {
  const stars = useMemo(() => {
    const starCount = {
      small: 800,  // Increased from 400
      medium: 200, // Increased from 100
      large: 100   // Increased from 50
    };

    let currentId = 0;
    return Object.entries(starCount).flatMap(([size, count]) =>
      Array.from({ length: count }, () => {
        const uniqueId = `star-${size}-${currentId++}`;
        return {
          id: uniqueId,
          size: size as 'small' | 'medium' | 'large',
          style: {
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 8}s`,
            opacity: Math.random() * 0.7 + 0.3,
          },
        };
      })
    );
  }, []);

  const [shootingStars, setShootingStars] = useState<ShootingStar[]>([]);

  const createShootingStar = useCallback(() => {
    const newStar: ShootingStar = {
      id: `shooting-star-${Date.now()}-${Math.random()}`,
      style: {
        top: `${Math.random() * 50}%`,
        left: '-10%',
      },
    };
    
    setShootingStars(prev => [...prev, newStar]);
    setTimeout(() => {
      setShootingStars(prev => prev.filter(star => star.id !== newStar.id));
    }, 3000);
  }, []);

  useEffect(() => {
    const interval = setInterval(createShootingStar, 8000);
    return () => clearInterval(interval);
  }, [createShootingStar]);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      <div className="absolute inset-0 bg-gradient-radial from-transparent to-black/40" />
      {stars.map((star) => (
        <div
          key={star.id}
          className={`star star-${star.size}`}
          style={star.style}
        />
      ))}
      {shootingStars.map((star) => (
        <div
          key={star.id}
          className="shooting-star"
          style={star.style}
        />
      ))}
    </div>
  );
}