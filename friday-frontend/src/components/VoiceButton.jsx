import { Mic, MicOff } from 'lucide-react';

export default function VoiceButton({ isListening, onToggle }) {
  return (
    <button
      id="voice-btn"
      onClick={onToggle}
      className={`voice-btn ${isListening ? 'voice-btn-active' : ''}`}
      title={isListening ? 'Stop listening' : 'Start voice input'}
      aria-label="Toggle voice input"
    >
      {isListening ? <MicOff size={18} /> : <Mic size={18} />}

      {/* Pulse rings when active */}
      {isListening && (
        <>
          <span className="voice-ring voice-ring-1" />
          <span className="voice-ring voice-ring-2" />
          {/* Waveform bars */}
          <span className="voice-wave-wrap">
            {[...Array(5)].map((_, i) => (
              <span key={i} className="voice-wave-bar" style={{ animationDelay: `${i * 0.1}s` }} />
            ))}
          </span>
        </>
      )}
    </button>
  );
}
