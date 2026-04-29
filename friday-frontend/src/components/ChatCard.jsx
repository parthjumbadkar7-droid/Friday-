import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import VoiceButton from './VoiceButton';
import ToolIndicator from './ToolIndicator';
import { sendMessage, fetchWeather, fetchSearch } from '../utils/api';

// Detect if message implies a tool call
function detectToolIntent(text) {
  const lower = text.toLowerCase();
  if (/(weather|temperature|forecast|how hot|how cold|raining|climate).+(in|at|for)/.test(lower) ||
      /(what.?s the weather|weather in|weather at|temp in)/.test(lower)) {
    // Extract city name (crude but effective)
    const match = lower.match(/(?:weather|temperature|forecast|temp)\s+(?:in|at|for)?\s+([a-z\s]+)/);
    const city = match ? match[1].trim() : null;
    return city ? { type: 'weather', city } : null;
  }
  if (/(search|look up|find|what is|who is|define|meaning of|tell me about)/.test(lower)) {
    return { type: 'search', query: text };
  }
  return null;
}

export default function ChatCard({
  messages,
  setMessages,
  isListening,
  onVoiceToggle,
  transcript,
  setTranscript,
  speak,
  onNewMessage,
  toolState,
  setToolState,
  externalPrompt,
  clearExternalPrompt,
}) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Sync voice transcript → input field
  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  // Handle external prompts (LeftPanel clicks or Voice Auto-Send)
  useEffect(() => {
    if (externalPrompt) {
      setInput(externalPrompt);
      clearExternalPrompt();
      // Use setTimeout to ensure the state update processes before triggering send
      setTimeout(() => {
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) sendBtn.click();
      }, 50);
    }
  }, [externalPrompt, clearExternalPrompt]);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput('');
    onNewMessage(); // reset proactive timer

    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setLoading(true);
    setToolState(null);

    try {
      // Tool detection
      const toolIntent = detectToolIntent(text);
      let toolData = null;

      if (toolIntent) {
        setToolState({ type: toolIntent.type, status: 'loading', data: null });
        try {
          if (toolIntent.type === 'weather') {
            toolData = await fetchWeather(toolIntent.city);
          } else {
            toolData = await fetchSearch(toolIntent.query);
          }
          setToolState({ type: toolIntent.type, status: 'done', data: toolData });
        } catch {
          setToolState(null);
        }
      }

      // Build context for Groq — inject tool result if available
      let contextMessages = updatedMessages.map(({ role, content }) => ({ role, content }));
      if (toolData) {
        const toolContext = toolIntent.type === 'weather'
          ? `[Tool result — weather for ${toolData.city}: ${toolData.temperature}${toolData.unit}, ${toolData.condition}, humidity ${toolData.humidity}%, wind ${toolData.windspeed} km/h]`
          : `[Tool result — search for "${toolData.query}": ${toolData.answer || 'No direct answer.'} ${toolData.results?.map(r => r.text).slice(0, 2).join(' | ') || ''}]`;
        contextMessages = [
          ...contextMessages.slice(0, -1),
          { role: 'user', content: `${text}\n\n${toolContext}` },
        ];
      }

      const { reply, timestamp } = await sendMessage(contextMessages);
      const fridayMsg = { role: 'assistant', content: reply, timestamp };
      setMessages((prev) => [...prev, fridayMsg]);
      speak(reply);
    } catch (err) {
      const errMsg = {
        role: 'assistant',
        content: "Sorry, I ran into an issue connecting to my backend. Check that the server is running.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, setMessages, onNewMessage, setToolState, speak]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-card">
      {/* Messages area */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p className="chat-empty-line1">Good to see you, Parth.</p>
            <p className="chat-empty-line2">What's on your mind?</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {/* Tool indicator appears before FRIDAY's reply */}
        {toolState && <ToolIndicator toolState={toolState} />}

        {/* Loading indicator */}
        {loading && (
          <div className="msg-row msg-row-friday">
            <div className="msg-bubble msg-bubble-friday msg-typing">
              <span className="typing-dot" style={{ animationDelay: '0s' }} />
              <span className="typing-dot" style={{ animationDelay: '0.2s' }} />
              <span className="typing-dot" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="chat-input-bar">
        <VoiceButton isListening={isListening} onToggle={onVoiceToggle} />
        <input
          ref={inputRef}
          id="chat-input"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isListening ? "Listening... (Release Shift to send, Caps Lock to cancel)" : "Talk to FRIDAY... (Hold Shift to talk)"}
          disabled={loading}
          autoComplete="off"
        />
        <button
          id="send-btn"
          className="send-btn"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          aria-label="Send message"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}
