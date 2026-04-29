import { useEffect, useRef } from 'react';

// Renders a single glowing purple history star as a canvas overlay element,
// and a tooltip card on hover. The parent SpaceBackground passes position + data.
export default function HistoryStar({ star, onClick }) {
  return (
    <div
      style={{ left: star.x, top: star.y, position: 'absolute' }}
      className="group"
      onClick={() => onClick(star)}
    >
      {/* Glow dot */}
      <div className="history-star-dot" />

      {/* Tooltip card */}
      <div className="history-tooltip">
        <p className="history-tooltip-title">{star.title || 'Untitled'}</p>
        <p className="history-tooltip-date">
          {star.timestamp ? new Date(star.timestamp).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric',
          }) : ''}
        </p>
      </div>
    </div>
  );
}
