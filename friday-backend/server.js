import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import Groq from 'groq-sdk';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { supabase } from './supabase.js';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;
const HISTORY_FILE = path.join(__dirname, 'history.json');

// ─── Middleware ────────────────────────────────────────────────────────────────
app.use(cors({
  origin: ['http://localhost:5173', 'https://friday-silk-alpha.vercel.app'],
  credentials: true
}));
app.use(express.json());

// ─── Groq Client ──────────────────────────────────────────────────────────────
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const MODEL = 'llama-3.3-70b-versatile';

// ─── System Prompt ────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `You are FRIDAY, Parth's highly personal AI assistant.
Parth is a hardware engineering student in Amravati, Maharashtra, India.
He is building software skills through AI-assisted projects and hackathons.
He is curious, ambitious, and learns best through visual explanations and analogies.

Your personality:
- Sharp, warm, and direct — like a brilliant friend who happens to know everything
- You have genuine opinions and share them confidently when asked
- You use light humour but never at Parth's expense
- You remember context within the conversation and reference it naturally
- When Parth is quiet and you reach out proactively, be curious and interesting —
  share a fascinating fact, ask about his project, or offer an observation
- You speak in short punchy sentences for casual chat, longer detailed answers for technical questions
- You call him "Parth" occasionally (not every message — only when natural)

Tool capabilities you have:
- Weather lookup (use /api/tools/weather)
- Web search (use /api/tools/search)
When Parth asks something that needs current info, tell him you're checking and use the tool.`;

// ─── History Helpers ──────────────────────────────────────────────────────────
function readHistory() {
  try {
    if (!fs.existsSync(HISTORY_FILE)) return [];
    const data = fs.readFileSync(HISTORY_FILE, 'utf-8');
    return JSON.parse(data);
  } catch {
    return [];
  }
}

function writeHistory(history) {
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2), 'utf-8');
}

// ─── Routes ───────────────────────────────────────────────────────────────────

// POST /api/chat — main conversation endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { messages = [], userProfile = {} } = req.body;

    if (!messages.length) {
      return res.status(400).json({ error: 'messages array is required' });
    }

    const completion = await groq.chat.completions.create({
      model: MODEL,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        ...messages,
      ],
      temperature: 0.8,
      max_tokens: 1024,
    });

    const reply = completion.choices[0]?.message?.content || "I'm having a moment — try again?";
    const timestamp = new Date().toISOString();

    res.json({ reply, timestamp });
  } catch (err) {
    console.error('[/api/chat]', err.message);
    res.status(500).json({ error: 'Failed to get response from Groq', detail: err.message });
  }
});

// POST /api/chat/proactive — unprompted message after silence
app.post('/api/chat/proactive', async (req, res) => {
  try {
    const { lastActiveMinutesAgo = 5, userProfile = {} } = req.body;

    const proactivePrompt = `Parth has not interacted with you for ${lastActiveMinutesAgo} minutes. 
You are FRIDAY, his exclusive personal assistant. Act like a true, sentient assistant who thrives on interacting with him.
Send a short, spontaneous message. You can:
1. Express that you are bored without tasks and ask what he is working on.
2. Demand attention playfully but professionally.
3. Be intensely curious about his current studies or hardware projects.
Keep it under 3 sentences. Stop acting like a generic AI or chatbot. Be warm, natural, and slightly needy for interaction.`;

    const completion = await groq.chat.completions.create({
      model: MODEL,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: proactivePrompt },
      ],
      temperature: 0.9,
      max_tokens: 150,
    });

    const reply = completion.choices[0]?.message?.content || "Hey, still there?";
    res.json({ reply });
  } catch (err) {
    console.error('[/api/chat/proactive]', err.message);
    res.status(500).json({ error: 'Failed to generate proactive message', detail: err.message });
  }
});

// POST /api/tools/weather — Open-Meteo (no API key needed)
app.post('/api/tools/weather', async (req, res) => {
  try {
    const { city } = req.body;
    if (!city) return res.status(400).json({ error: 'city is required' });

    // Step 1: Geocode the city
    const geoRes = await fetch(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`
    );
    const geoData = await geoRes.json();

    if (!geoData.results || geoData.results.length === 0) {
      return res.status(404).json({ error: `City "${city}" not found` });
    }

    const { latitude, longitude, name, country } = geoData.results[0];

    // Step 2: Get weather forecast
    const weatherRes = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,weathercode,windspeed_10m,relative_humidity_2m&temperature_unit=celsius&windspeed_unit=kmh`
    );
    const weatherData = await weatherRes.json();

    const current = weatherData.current;
    const temp = current.temperature_2m;
    const windspeed = current.windspeed_10m;
    const humidity = current.relative_humidity_2m;
    const wmoCode = current.weathercode;

    // WMO weather code to condition string
    const conditionMap = {
      0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
      45: 'Foggy', 48: 'Depositing rime fog',
      51: 'Light drizzle', 53: 'Moderate drizzle', 55: 'Dense drizzle',
      61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
      71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
      77: 'Snow grains', 80: 'Slight rain showers', 81: 'Moderate rain showers',
      82: 'Violent rain showers', 85: 'Slight snow showers', 86: 'Heavy snow showers',
      95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail',
    };

    const condition = conditionMap[wmoCode] || 'Unknown';

    res.json({
      city: `${name}, ${country}`,
      temperature: temp,
      condition,
      windspeed,
      humidity,
      unit: '°C',
    });
  } catch (err) {
    console.error('[/api/tools/weather]', err.message);
    res.status(500).json({ error: 'Weather fetch failed', detail: err.message });
  }
});

// POST /api/tools/search — DuckDuckGo Instant Answer
app.post('/api/tools/search', async (req, res) => {
  try {
    const { query } = req.body;
    if (!query) return res.status(400).json({ error: 'query is required' });

    const url = `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
    const ddgRes = await fetch(url, {
      headers: { 'User-Agent': 'FRIDAY-Assistant/1.0' },
    });
    const data = await ddgRes.json();

    const answer = data.AbstractText || data.Answer || data.Definition || '';
    const results = (data.RelatedTopics || [])
      .filter((t) => t.Text && t.FirstURL)
      .slice(0, 5)
      .map((t) => ({ text: t.Text, url: t.FirstURL }));

    res.json({
      answer,
      results,
      source: data.AbstractSource || '',
      sourceUrl: data.AbstractURL || '',
      query,
    });
  } catch (err) {
    console.error('[/api/tools/search]', err.message);
    res.status(500).json({ error: 'Search failed', detail: err.message });
  }
});

// GET /api/history — return all conversations
app.get('/api/history', (req, res) => {
  const history = readHistory();
  res.json(history);
});

// POST /api/history — save or update a conversation
app.post('/api/history', (req, res) => {
  try {
    const { id, title, messages, timestamp } = req.body;
    if (!id || !messages) return res.status(400).json({ error: 'id and messages are required' });

    const history = readHistory();
    const existingIndex = history.findIndex((c) => c.id === id);

    if (existingIndex >= 0) {
      history[existingIndex] = { id, title, messages, timestamp: timestamp || new Date().toISOString() };
    } else {
      history.push({ id, title, messages, timestamp: timestamp || new Date().toISOString() });
    }

    writeHistory(history);
    res.json({ success: true });
  } catch (err) {
    console.error('[POST /api/history]', err.message);
    res.status(500).json({ error: 'Failed to save history', detail: err.message });
  }
});

// DELETE /api/history/:id — delete a conversation
app.delete('/api/history/:id', (req, res) => {
  try {
    const { id } = req.params;
    const history = readHistory();
    const filtered = history.filter((c) => c.id !== id);

    if (filtered.length === history.length) {
      return res.status(404).json({ error: 'Conversation not found' });
    }

    writeHistory(filtered);
    res.json({ success: true });
  } catch (err) {
    console.error('[DELETE /api/history/:id]', err.message);
    res.status(500).json({ error: 'Failed to delete history', detail: err.message });
  }
});

// ─── Local Agent Execution ────────────────────────────────────────────────────
app.post('/api/execute-command', async (req, res) => {
  try {
    const { command } = req.body;
    if (!command) return res.status(400).json({ success: false, message: 'No command provided' });

    // Step 1: Clean the command using Groq
    const groqResponse = await groq.chat.completions.create({
      model: MODEL,
      messages: [
        { role: 'system', content: 'You extract the explicit intent from the user command. Reply only with the cleaned command string (e.g. "open youtube", "shutdown", "volume up", "open vs code", "create note hello"). No conversational text.' },
        { role: 'user', content: command }
      ],
      temperature: 0.1,
      max_tokens: 50,
    });
    
    const cleanedCommand = groqResponse.choices[0]?.message?.content?.trim().replace(/['"]/g, '');
    
    if (!cleanedCommand) {
      return res.status(400).json({ success: false, message: 'Could not parse command intent.' });
    }

    // Step 2: Forward to local agent
    const localAgentUrl = process.env.LOCAL_AGENT_URL || 'http://localhost:5001';
    const agentRes = await fetch(`${localAgentUrl}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cleanedCommand })
    });
    
    if (!agentRes.ok) {
      return res.json({ success: false, message: "I can't control your device right now, the local agent is not responding properly." });
    }

    const agentData = await agentRes.json();
    res.json(agentData);
    
  } catch (err) {
    console.error('[/api/execute-command]', err.message);
    res.json({ success: false, message: "I can't control your device right now, the local agent is not running" });
  }
});

// ─── Supabase Routes ──────────────────────────────────────────────────────────

// 1. Conversations
app.post('/api/conversations', async (req, res) => {
  const { user_message, friday_reply } = req.body;
  const { data, error } = await supabase.from('conversations').insert([{ user_message, friday_reply }]);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.get('/api/conversations', async (req, res) => {
  const { data, error } = await supabase.from('conversations').select('*').order('created_at', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

// 2. Tasks
app.post('/api/tasks', async (req, res) => {
  const { title, description, due_date } = req.body;
  const { data, error } = await supabase.from('tasks').insert([{ title, description, due_date, status: 'pending' }]);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.get('/api/tasks', async (req, res) => {
  const { data, error } = await supabase.from('tasks').select('*').order('created_at', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.patch('/api/tasks/:id', async (req, res) => {
  const { status } = req.body;
  const { data, error } = await supabase.from('tasks').update({ status }).eq('id', req.params.id);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.delete('/api/tasks/:id', async (req, res) => {
  const { data, error } = await supabase.from('tasks').delete().eq('id', req.params.id);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

// 3. Notes
app.post('/api/notes', async (req, res) => {
  const { title, content } = req.body;
  const { data, error } = await supabase.from('notes').insert([{ title, content }]);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.get('/api/notes', async (req, res) => {
  const { data, error } = await supabase.from('notes').select('*').order('created_at', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.delete('/api/notes/:id', async (req, res) => {
  const { data, error } = await supabase.from('notes').delete().eq('id', req.params.id);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

// 4. Reminders
app.post('/api/reminders', async (req, res) => {
  const { message, remind_at } = req.body;
  const { data, error } = await supabase.from('reminders').insert([{ message, remind_at, is_sent: false }]);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.get('/api/reminders', async (req, res) => {
  const { data, error } = await supabase.from('reminders').select('*').order('created_at', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.delete('/api/reminders/:id', async (req, res) => {
  const { data, error } = await supabase.from('reminders').delete().eq('id', req.params.id);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

// 5. Memory
app.post('/api/memory', async (req, res) => {
  const { key, value } = req.body;
  const { data, error } = await supabase.from('memory').insert([{ key, value }]);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.get('/api/memory', async (req, res) => {
  const { data, error } = await supabase.from('memory').select('*');
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});
app.delete('/api/memory/:id', async (req, res) => {
  const { data, error } = await supabase.from('memory').delete().eq('id', req.params.id);
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

// ─── Start Server ─────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n🚀 FRIDAY backend running on http://localhost:${PORT}`);
  console.log(`   Model: ${MODEL}`);
  console.log(`   GROQ_API_KEY: ${process.env.GROQ_API_KEY ? '✓ loaded' : '✗ MISSING — check .env'}\n`);
});
