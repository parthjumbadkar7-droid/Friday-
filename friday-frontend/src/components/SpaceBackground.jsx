import { useEffect, useRef, useMemo } from 'react';
import HistoryStar from './HistoryStar';

const NUM_STARS = 150;

function randomBetween(a, b) {
  return a + Math.random() * (b - a);
}

function generateStars(w, h) {
  return Array.from({ length: NUM_STARS }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: randomBetween(0.4, 1.8),
    baseOpacity: randomBetween(0.3, 1),
    speed: randomBetween(0.3, 1.2),
    phase: Math.random() * Math.PI * 2,
  }));
}

export default function SpaceBackground({ historyConversations, onHistoryClick }) {
  const canvasRef = useRef(null);
  const starsRef = useRef([]);
  const animRef = useRef(null);

  // Assign fixed random positions to history conversations (stable per session)
  const historyStars = useMemo(() => {
    if (!historyConversations?.length) return [];
    const w = window.innerWidth;
    const h = window.innerHeight;
    // keep history stars away from center nebula (center 30% radius)
    return historyConversations.map((conv, i) => {
      let x, y;
      do {
        x = Math.random() * w;
        y = Math.random() * h;
      } while (
        Math.abs(x - w / 2) < w * 0.25 &&
        Math.abs(y - h / 2) < h * 0.25
      );
      return { ...conv, x, y };
    });
  }, [historyConversations]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      starsRef.current = generateStars(canvas.width, canvas.height);
    };
    resize();
    window.addEventListener('resize', resize);

    const draw = (t) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      starsRef.current.forEach((star) => {
        const opacity = star.baseOpacity * (0.5 + 0.5 * Math.sin(t * 0.001 * star.speed + star.phase));
        ctx.save();
        ctx.globalAlpha = opacity;
        const isLarger = star.r > 1.4;
        if (isLarger) {
          // Larger stars get a faint purple glow
          const grd = ctx.createRadialGradient(star.x, star.y, 0, star.x, star.y, star.r * 4);
          grd.addColorStop(0, 'rgba(180, 140, 255, 0.8)');
          grd.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = grd;
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.r * 4, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.fillStyle = isLarger ? '#c4b5fd' : '#e0e8ff';
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });
      animRef.current = requestAnimationFrame(draw);
    };
    animRef.current = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animRef.current);
    };
  }, []);

  return (
    <div className="space-bg">
      <canvas ref={canvasRef} className="star-canvas" />
      {/* Overlay history stars as DOM elements so hover/click works */}
      {historyStars.map((star) => (
        <HistoryStar key={star.id} star={star} onClick={onHistoryClick} />
      ))}
    </div>
  );
}
