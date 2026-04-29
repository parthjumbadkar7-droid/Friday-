import { useState, useEffect, useCallback, useRef } from 'react';
import { Volume2, VolumeX, Clock } from 'lucide-react';
import AuraSwarm from './components/AuraSwarm';
import SpaceBackground from './components/SpaceBackground'; // keep as option or layered
import Nebula from './components/Nebula';
import ChatCard from './components/ChatCard';
import LeftPanel from './components/LeftPanel';
import { useVoice } from './hooks/useVoice';
import { useProactive } from './hooks/useProactive';
import { useHistory } from './hooks/useHistory';
import { v4 as uuidv4 } from 'uuid';

const USER_PROFILE = {
  name: 'Parth',
  location: 'Amravati, Maharashtra, India',
  field: 'Hardware Engineering Student',
};

// Auto-generate a title from the first user message
function generateTitle(messages) {
  const first = messages.find((m) => m.role === 'user');
  if (!first) return 'New Conversation';
  return first.content.slice(0, 48) + (first.content.length > 48 ? '…' : '');
}

function LiveClock() {
  const [time, setTime] = useState('');
  useEffect(() => {
    const update = () =>
      setTime(
        new Date().toLocaleTimeString('en-IN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        })
      );
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="clock-text">{time}</span>;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [toolState, setToolState] = useState(null);
  const [externalPrompt, setExternalPrompt] = useState(null);
  const convIdRef = useRef(uuidv4());

  const { history, loaded, loadHistory, saveConversation, removeConversation } = useHistory();

  const { isListening, transcript, setTranscript, startListening, stopListening, speak, cancelSpeech, selectedVoice } =
    useVoice({ voiceEnabled });

  const shiftPressedRef = useRef(false);

  // Push-to-Talk global key listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is already typing in an input field (so shift works normally for capitals)
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      if (e.key === 'Shift' && !shiftPressedRef.current) {
        shiftPressedRef.current = true;
        startListening();
      }
      if (e.key === 'CapsLock' && shiftPressedRef.current) {
        shiftPressedRef.current = false;
        cancelSpeech();
        stopListening();
        setTranscript('');
      }
    };

    const handleKeyUp = (e) => {
      if (e.key === 'Shift' && shiftPressedRef.current) {
        shiftPressedRef.current = false;
        stopListening();
        
        // After releasing, we take whatever the latest transcript is and send it
        // We use a small timeout to let the final 'onresult' from Web Speech fire if it hasn't yet
        setTimeout(() => {
          setTranscript((currentText) => {
            if (currentText.trim()) {
              setExternalPrompt(currentText);
            }
            return ''; // clear it out
          });
        }, 300);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [startListening, stopListening, cancelSpeech, setTranscript]);

  // Wrap speak to set isSpeaking state for nebula glow
  // Uses the selected voice from useVoice so the sweet female voice is applied
  const speakWithState = useCallback(
    (text) => {
      if (!voiceEnabled) return;
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      if (selectedVoice.current) utter.voice = selectedVoice.current;
      utter.rate = 0.95;   // warm, natural pace
      utter.pitch = 1.15;  // sweet, slightly higher tone
      utter.volume = 1.0;
      setIsSpeaking(true);
      utter.onend = () => setIsSpeaking(false);
      utter.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utter);
    },
    [voiceEnabled, selectedVoice]
  );

  // Load conversation history on mount
  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Auto-save conversation when ≥ 3 messages exchanged
  useEffect(() => {
    if (messages.length >= 3) {
      const conversation = {
        id: convIdRef.current,
        title: generateTitle(messages),
        messages,
        timestamp: new Date().toISOString(),
      };
      saveConversation(conversation);
    }
  }, [messages, saveConversation]);

  // Handle proactive message
  const handleProactive = useCallback((reply) => {
    const msg = {
      role: 'assistant',
      content: reply,
      timestamp: new Date().toISOString(),
      proactive: true,
    };
    setMessages((prev) => [...prev, msg]);
    speakWithState(reply);
  }, [speakWithState]);

  const { resetTimer } = useProactive(handleProactive);

  const handleNewMessage = useCallback(() => {
    resetTimer();
  }, [resetTimer]);

  // Load a history conversation into chat
  const handleHistoryLoad = useCallback((star) => {
    if (star.messages) {
      convIdRef.current = star.id;
      setMessages(star.messages);
    }
  }, []);

  const toggleVoice = () => {
    if (voiceEnabled) window.speechSynthesis.cancel();
    setVoiceEnabled((v) => !v);
  };

  const handleVoiceToggle = () => {
    if (isListening) stopListening();
    else startListening();
  };

  return (
    <div className="app-root">
      {/* 3D Particle Swarm Background (Water as Archive) */}
      <AuraSwarm />
      
      {/* Deep space animated background layered behind or merged */}
      <SpaceBackground
        historyConversations={history}
        onHistoryClick={handleHistoryLoad}
      />

      {/* Nebula glow orb */}
      <Nebula isSpeaking={isSpeaking} />

      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-title">
          <span className="friday-logo">F R I D A Y</span>
          <span className="friday-version">v2.0</span>
        </div>
        <div className="header-right">
          <Clock size={14} className="clock-icon" />
          <LiveClock />
          <button
            id="voice-toggle-btn"
            onClick={toggleVoice}
            className="voice-toggle-btn"
            title={voiceEnabled ? 'Mute FRIDAY voice' : 'Enable FRIDAY voice'}
            aria-label="Toggle voice output"
          >
            {voiceEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
        </div>
      </header>

      {/* ── Chat interface ── */}
      <main className="app-main">
        <LeftPanel
          messageCount={messages.length}
          onPromptClick={(text) => setExternalPrompt(text)}
        />
        <ChatCard
          messages={messages}
          setMessages={setMessages}
          isListening={isListening}
          onVoiceToggle={handleVoiceToggle}
          transcript={transcript}
          setTranscript={setTranscript}
          speak={speakWithState}
          onNewMessage={handleNewMessage}
          toolState={toolState}
          setToolState={setToolState}
          externalPrompt={externalPrompt}
          clearExternalPrompt={() => setExternalPrompt(null)}
        />
      </main>
    </div>
  );
}
