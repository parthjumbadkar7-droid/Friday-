import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import VoiceButton from './VoiceButton';
import ToolIndicator from './ToolIndicator';
import { sendMessage, fetchWeather, fetchSearch, executeCommand } from '../utils/api';

// ── Startup Greeting ──────────────────────────────────────────────
async function buildGreeting() {
  const now = new Date();
  const h = now.getHours();
  const period = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const day = days[now.getDay()];

  let weatherLine = '';
  try {
    const wr = await fetch(
      'https://api.open-meteo.com/v1/forecast?latitude=20.93&longitude=77.75&current_weather=true'
    );
    const wj = await wr.json();
    const temp = wj?.current_weather?.temperature;
    const code = wj?.current_weather?.weathercode;
    const desc = code <= 1 ? 'clear skies' : code <= 3 ? 'partly cloudy' : code <= 67 ? 'rain' : 'overcast';
    if (temp !== undefined) weatherLine = ` It's ${temp}°C with ${desc} in Amravati.`;
  } catch { /* skip weather silently */ }

  const greetings = [
    `Good ${period}, Parth! Happy ${day}.${weatherLine} What are we building today?`,
    `Hey Parth — ${day} ${period}.${weatherLine} I'm ready when you are. What's the mission?`,
    `Good ${period}!${weatherLine} It's ${day} — what's on the agenda?`,
    `${day} ${period}, Parth.${weatherLine} Systems online. What do you need?`,
    `Good ${period}, Parth.${weatherLine} Another ${day}, another chance to build something great. Where do we start?`,
    `Hey — glad you're here.${weatherLine} It's ${day} ${period}. What are we working on?`,
  ];
  return greetings[Math.floor(Math.random() * greetings.length)];
}

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
  onEditMessage,
  onNewChat,
}) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionResults, setActionResults] = useState([]);
  const [followUp, setFollowUp] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-greeting on first load
  useEffect(() => {
    if (messages.length > 0) return;
    const timer = setTimeout(async () => {
      const greeting = await buildGreeting();
      const greetMsg = { role: 'assistant', content: greeting, timestamp: new Date().toISOString() };
      setMessages(prev => prev.length === 0 ? [greetMsg] : prev);
      speak(greeting);
    }, 1500);
    return () => clearTimeout(timer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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

    // Session Management Detection
    const lowerText = text.toLowerCase();
    if (lowerText === 'new chat' || lowerText === 'open new chat box' || lowerText === 'start new session') {
      onNewChat();
      setInput('');
      return;
    }

    setInput('');
    onNewMessage(); // reset proactive timer

    const isRetry = text.toLowerCase() === 'try again';
    let userMsg = null;
    let updatedMessages = [...messages];

    if (isRetry) {
      // Find last user message to retry
      const lastUserIdx = [...messages].reverse().findIndex(m => m.role === 'user');
      if (lastUserIdx === -1) {
        setMessages(prev => [...prev, { role: 'assistant', content: "I don't have a previous request to try again.", timestamp: new Date().toISOString() }]);
        setLoading(false);
        return;
      }
      const actualIdx = messages.length - 1 - lastUserIdx;
      userMsg = messages[actualIdx];
      updatedMessages = messages.slice(0, actualIdx + 1);
    } else {
      userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
      updatedMessages = [...messages, userMsg];
    }

    setMessages(updatedMessages);
    setLoading(true);
    setToolState(null);

    const queryText = userMsg.content;

    try {
      // Tool detection
      const toolIntent = detectToolIntent(queryText);
      let toolData = null;

      if (toolIntent) {
        setToolState({ type: toolIntent.type, status: 'loading', data: null });
        try {
          if (toolIntent.type === 'weather') {
            toolData = await fetchWeather(toolIntent.city);
          } else if (toolIntent.type === 'search') {
            toolData = await fetchSearch(toolIntent.query);
          } else if (toolIntent.type === 'system') {
            toolData = await executeCommand(toolIntent.command);
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
          { role: 'user', content: `${queryText}\n\n${toolContext}` },
        ];
      }

      const isCommand = (msg) => {
        const triggers = ['open', 'play', 'download', 'send', 'search', 'close', 'screenshot', 'lock', 'shutdown', 'volume', 'restart', 'type'];
        return triggers.some(t => msg.toLowerCase().startsWith(t));
      };

      const endpoint = isCommand(queryText) ? '/api/agent/command' : '/api/chat';
      const res = await fetch(`${import.meta.env.VITE_API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: queryText, history: contextMessages })
      });

      if (!res.ok) throw new Error('Backend error');
      const data = await res.json();
      let reply = data.reply || "Done!";

      // If reply looks like raw JSON, extract just the reply field
      if (typeof reply === 'string' && reply.trim().startsWith('{')) {
        try {
          const parsed = JSON.parse(reply);
          reply = parsed.reply || "Done!";
        } catch {}
      }

      const results = data.results || [];
      const fu = data.follow_up || null;

      const fridayMsg = {
        role: 'assistant',
        content: reply,
        timestamp: new Date().toISOString(),
        actionResults: results,
        followUp: fu,
      };
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
          <div key={i}>
            <MessageBubble message={msg} onEdit={onEditMessage} />
            {msg.actionResults && msg.actionResults.length > 0 && (
              <div className="action-results">
                {msg.actionResults.map((r, ri) => (
                  <div key={ri} className="action-result-line">› {r}</div>
                ))}
              </div>
            )}
            {msg.followUp && (
              <button
                className="follow-up-chip"
                onClick={() => setExternalPrompt ? setExternalPrompt(msg.followUp) : null}
              >
                {msg.followUp}
              </button>
            )}
          </div>
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
