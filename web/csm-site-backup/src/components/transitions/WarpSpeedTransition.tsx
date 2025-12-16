import React, { useEffect, useRef } from 'react';

interface WarpSpeedTransitionProps {
  isActive: boolean;
  onComplete: () => void;
}

export function WarpSpeedTransition({ isActive, onComplete }: WarpSpeedTransitionProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestRef = useRef<number>();
  const starsRef = useRef<{ x: number; y: number; z: number; }[]>([]);

  useEffect(() => {
    if (!isActive) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize stars
    const initStars = () => {
      starsRef.current = Array.from({ length: 1000 }, () => ({
        x: (Math.random() - 0.5) * 2000,
        y: (Math.random() - 0.5) * 2000,
        z: Math.random() * 2000
      }));
    };
    initStars();

    let speed = 0;
    const maxSpeed = 50;
    const acceleration = 0.2;

    const animate = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      speed = Math.min(speed + acceleration, maxSpeed);

      starsRef.current.forEach((star, i) => {
        star.z -= speed;

        if (star.z <= 1) {
          star.z = 2000;
          star.x = (Math.random() - 0.5) * 2000;
          star.y = (Math.random() - 0.5) * 2000;
        }

        const x = (star.x / star.z) * 500 + centerX;
        const y = (star.y / star.z) * 500 + centerY;
        const size = Math.max(0, (1 - star.z / 2000) * 3);

        ctx.beginPath();
        ctx.fillStyle = `rgba(255, 255, 255, ${1 - star.z / 2000})`;
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();

        // Draw trail
        const prevX = (star.x / (star.z + speed * 2)) * 500 + centerX;
        const prevY = (star.y / (star.z + speed * 2)) * 500 + centerY;
        ctx.beginPath();
        ctx.strokeStyle = `rgba(255, 255, 255, ${(1 - star.z / 2000) * 0.5})`;
        ctx.lineWidth = size * 0.5;
        ctx.moveTo(x, y);
        ctx.lineTo(prevX, prevY);
        ctx.stroke();
      });

      if (speed >= maxSpeed) {
        setTimeout(() => {
          onComplete();
        }, 1000);
        return;
      }

      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [isActive, onComplete]);

  if (!isActive) return null;

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-50 pointer-events-none"
      style={{ opacity: isActive ? 1 : 0 }}
    />
  );
}