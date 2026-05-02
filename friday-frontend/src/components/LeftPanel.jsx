import { useState, useEffect } from 'react';
import { Trash2 } from 'lucide-react';

const TIPS = [
  "Neurons that fire together, wire together — that's why spaced repetition beats cramming by 2x.",
  "In hardware, signal integrity is everything. In code, same rule applies to data integrity.",
  "The fastest way to learn a new framework: build something real with it in under 48 hours.",
  "LLaMA 3 has 70B parameters — roughly 140 GB of floating-point numbers that 'think'.",
  "Sleep consolidates memory. Studying before bed + a good night's sleep beats 3 AM sessions.",
  "VHDL and Verilog are to hardware what Python is to AI — the native language of the domain.",
  "Every great engineer writes terrible first drafts. Iteration is the job.",
  "Hackathons aren't about winning — they're about compressing 3 months of learning into 36 hours.",
  "The best debugger is still a piece of paper and a fresh set of eyes.",
  "Amravati has produced some brilliant minds. You're in good company.",
];

const PROMPTS = [
  { icon: '🌤️', text: 'Weather in Amravati?' },
  { icon: '🧠', text: 'Give me a tech fact' },
  { icon: '📚', text: 'What should I learn today?' },
  { icon: '🐛', text: 'Help me debug code' },
  { icon: '🚀', text: 'Hackathon project idea' },
  { icon: '⚡', text: 'Explain like I\'m 18' },
];

const MOODS = [
  { emoji: '🔥', label: 'Fired up' },
  { emoji: '😎', label: 'Focused' },
  { emoji: '😴', label: 'Tired' },
  { emoji: '🤔', label: 'Curious' },
  { emoji: '😤', label: 'Grinding' },
];

function useLiveStats() {
  const [stats, setStats] = useState({ hour: '--', day: '--', session: '0' });
  useEffect(() => {
    const sessionStart = Date.now();
    const update = () => {
      const now = new Date();
      const h = now.getHours();
      const greeting = h < 12 ? 'Morning' : h < 17 ? 'Afternoon' : h < 21 ? 'Evening' : 'Night';
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const mins = Math.floor((Date.now() - sessionStart) / 60000);
      setStats({
        greeting,
        day: days[now.getDay()],
        session: mins < 1 ? '<1m' : `${mins}m`,
      });
    };
    update();
    const id = setInterval(update, 10000);
    return () => clearInterval(id);
  }, []);
  return stats;
}

export default function LeftPanel({ onPromptClick, messageCount, history, onHistoryClick, onNewChat, onDeleteHistory }) {
  const [agentStatus, setAgentStatus] = useState('offline');
  
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/api/agent/status`);
        const data = await res.json();
        setAgentStatus(data.status);
      } catch {
        setAgentStatus('offline');
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);
  const [note, setNote] = useState(() => localStorage.getItem('friday_note') || '');
  const [mood, setMood] = useState(null);
  const stats = useLiveStats();
  const [tipIndex] = useState(() => Math.floor(Math.random() * TIPS.length));

  const handleNoteChange = (e) => {
    setNote(e.target.value);
    localStorage.setItem('friday_note', e.target.value);
  };

  const clearNote = () => {
    setNote('');
    localStorage.removeItem('friday_note');
  };

  return (
    <div className="left-panel">

      {/* ── Profile Card ── */}
      <div className="panel-card">
        <div className="profile-card">
          <div className="profile-avatar">P</div>
          <div className="profile-info">
            <div className="profile-name">Parth</div>
            <div className="profile-role">Hardware Eng. Student · Amravati</div>
            <div className="profile-status">
              <span className={`status-dot ${agentStatus === 'online' ? 'status-online' : 'status-offline'}`} />
              <span className="status-text">{agentStatus === 'online' ? 'FRIDAY is online' : 'Agent offline'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Live Stats ── */}
      <div className="panel-card">
        <div className="panel-card-title">Session Stats</div>
        <div className="stats-row">
          <div className="stat-box">
            <div className="stat-value">{stats.greeting || '--'}</div>
            <div className="stat-label">Period</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{stats.day}</div>
            <div className="stat-label">Today</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{stats.session}</div>
            <div className="stat-label">Online</div>
          </div>
          <div className="stat-box">
            <div className="stat-value">{messageCount}</div>
            <div className="stat-label">Msgs</div>
          </div>
        </div>
      </div>

      {/* ── Mood Tracker ── */}
      <div className="panel-card">
        <div className="panel-card-title">How are you feeling?</div>
        <div className="mood-row">
          {MOODS.map((m) => (
            <button
              key={m.emoji}
              className={`mood-btn ${mood === m.emoji ? 'mood-selected' : ''}`}
              onClick={() => setMood(m.emoji)}
              title={m.label}
            >
              {m.emoji}
            </button>
          ))}
        </div>
        {mood && (
          <div className="mood-label">
            {MOODS.find(m => m.emoji === mood)?.label} — FRIDAY noticed 👀
          </div>
        )}
      </div>

      {/* ── Quick Prompts ── */}
      <div className="panel-card">
        <div className="panel-card-title">Quick Fire</div>
        <div className="prompt-grid">
          {PROMPTS.map((p) => (
            <button
              key={p.text}
              className="prompt-chip"
              onClick={() => onPromptClick(p.text)}
              title={`Ask FRIDAY: ${p.text}`}
            >
              <span className="prompt-chip-icon">{p.icon}</span>
              {p.text}
            </button>
          ))}
        </div>
      </div>

      {/* ── History List ── */}
      <div className="panel-card">
        <div className="panel-card-title flex justify-between items-center">
          <span>Recent Conversations</span>
          <button 
            onClick={onNewChat}
            className="text-xs bg-purple-600/30 hover:bg-purple-600/60 text-purple-200 px-2 py-1 rounded transition-colors"
          >
            + New
          </button>
        </div>
        <div className="flex flex-col gap-2 max-h-40 overflow-y-auto pr-1">
          {history && history.length > 0 ? (
            history.slice().reverse().slice(0, 5).map((conv) => (
              <div key={conv.id} className="flex items-center group">
                <button
                  className="flex-1 text-left text-sm text-gray-300 hover:text-white hover:bg-white/5 p-2 rounded transition-colors whitespace-nowrap overflow-hidden overflow-ellipsis"
                  onClick={() => onHistoryClick(conv)}
                  title={conv.title}
                >
                  {conv.title}
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteHistory(conv.id); }}
                  className="opacity-0 group-hover:opacity-100 p-2 text-gray-500 hover:text-red-400 transition-all"
                  title="Delete conversation"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          ) : (
            <div className="text-sm text-gray-500">No recent chats</div>
          )}
        </div>
      </div>

      {/* ── Notepad ── */}
      <div className="panel-card">
        <div className="panel-card-title">Quick Notes</div>
        <textarea
          className="notepad-textarea"
          value={note}
          onChange={handleNoteChange}
          placeholder="Jot something down... ideas, snippets, links..."
          rows={4}
        />
        <div className="notepad-footer">
          {note && (
            <button className="notepad-clear-btn" onClick={clearNote}>
              Clear note
            </button>
          )}
        </div>
      </div>

      {/* ── Tip of the Day ── */}
      <div className="panel-card tip-card">
        <div className="tip-label">💡 Parth's Daily Insight</div>
        <div className="tip-text">{TIPS[tipIndex]}</div>
      </div>

    </div>
  );
}
