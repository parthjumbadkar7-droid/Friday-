// All API calls to the FRIDAY backend
const BASE = '/api';

export async function sendMessage(messages, userProfile = {}) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, userProfile }),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.status}`);
  return res.json(); // { reply, timestamp }
}

export async function sendProactive(lastActiveMinutesAgo = 5, userProfile = {}) {
  const res = await fetch(`${BASE}/chat/proactive`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lastActiveMinutesAgo, userProfile }),
  });
  if (!res.ok) throw new Error(`Proactive error: ${res.status}`);
  return res.json(); // { reply }
}

export async function fetchWeather(city) {
  const res = await fetch(`${BASE}/tools/weather`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city }),
  });
  if (!res.ok) throw new Error(`Weather error: ${res.status}`);
  return res.json();
}

export async function fetchSearch(query) {
  const res = await fetch(`${BASE}/tools/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Search error: ${res.status}`);
  return res.json();
}

export async function getHistory() {
  const res = await fetch(`${BASE}/history`);
  if (!res.ok) throw new Error(`History fetch error: ${res.status}`);
  return res.json();
}

export async function saveHistory(conversation) {
  const res = await fetch(`${BASE}/history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(conversation),
  });
  if (!res.ok) throw new Error(`History save error: ${res.status}`);
  return res.json();
}

export async function deleteHistory(id) {
  const res = await fetch(`${BASE}/history/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`History delete error: ${res.status}`);
  return res.json();
}

export async function executeCommand(command) {
  const res = await fetch(`${BASE}/execute-command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command }),
  });
  if (!res.ok) throw new Error(`Execute command error: ${res.status}`);
  return res.json(); // { success, message }
}
