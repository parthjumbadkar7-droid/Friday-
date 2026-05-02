/**
 * friday-backend/routes/agent.js
 * 
 * Handles:
 *  - POST /api/agent/heartbeat   ← agent pings this every 15s
 *  - GET  /api/agent/status      ← frontend polls this to show online/offline
 *  - POST /api/agent/command     ← frontend sends natural language commands
 *  - POST /api/agent/execute     ← frontend sends direct actions
 */

import express from 'express';
import axios from 'axios';

const router = express.Router();

const AGENT_SECRET = process.env.AGENT_SECRET || 'friday-secret-2024';

// In-memory state (resets on Render restart, that's fine)
let agentState = {
  status: 'offline',
  url: process.env.LOCAL_AGENT_URL || null,
  lastHeartbeat: null,
  lastSeen: null,
};

// ──────────────────────────────────────────────
//  HEARTBEAT  (called by Python agent every 15s)
// ──────────────────────────────────────────────
router.post('/heartbeat', (req, res) => {
  const { secret, status } = req.body;

  if (secret !== AGENT_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  agentState.status = status || 'online';
  agentState.lastHeartbeat = Date.now();
  agentState.lastSeen = new Date().toISOString();

  return res.json({ ok: true, received: agentState.lastSeen });
});

// ──────────────────────────────────────────────
//  STATUS  (polled by frontend every 10s)
// ──────────────────────────────────────────────
router.get('/status', (req, res) => {
  const now = Date.now();
  const TIMEOUT_MS = 30_000; // 30 seconds

  // If last heartbeat was > 30s ago, mark offline
  if (!agentState.lastHeartbeat || now - agentState.lastHeartbeat > TIMEOUT_MS) {
    agentState.status = 'offline';
  }

  return res.json({
    status: agentState.status,
    lastSeen: agentState.lastSeen,
    agentUrl: agentState.url,
  });
});

// ──────────────────────────────────────────────
//  REGISTER AGENT URL  (called by start_friday.py)
// ──────────────────────────────────────────────
router.post('/register', (req, res) => {
  const { url, secret } = req.body;

  // Accept with or without secret for backwards compatibility
  if (secret && secret !== AGENT_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  agentState.url = url;
  agentState.status = 'online';
  agentState.lastHeartbeat = Date.now();
  agentState.lastSeen = new Date().toISOString();

  console.log(`✓ Agent registered: ${url}`);
  return res.json({ ok: true, url });
});

// ──────────────────────────────────────────────
//  COMMAND  (natural language → agent AI loop)
// ──────────────────────────────────────────────
router.post('/command', async (req, res) => {
  if (agentState.status !== 'online' || !agentState.url) {
    return res.status(503).json({
      error: 'Agent is offline',
      hint: 'Make sure start_friday.py is running on your laptop',
    });
  }

  const { message, history } = req.body;

  if (!message) {
    return res.status(400).json({ error: 'message is required' });
  }

  try {
    const response = await axios.post(
      `${agentState.url}/api/command`,
      { message, history, secret: AGENT_SECRET },
      { timeout: 20_000 }
    );
    return res.json(response.data);
  } catch (err) {
    const detail = err.response?.data || err.message;
    console.error('Agent command error:', detail);

    // If agent is unreachable, mark it offline
    if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
      agentState.status = 'offline';
    }

    return res.status(502).json({ error: 'Agent did not respond', detail });
  }
});

// ──────────────────────────────────────────────
//  EXECUTE  (direct action list, no AI)
// ──────────────────────────────────────────────
router.post('/execute', async (req, res) => {
  if (agentState.status !== 'online' || !agentState.url) {
    return res.status(503).json({ error: 'Agent is offline' });
  }

  const { actions } = req.body;

  try {
    const response = await axios.post(
      `${agentState.url}/api/execute`,
      { actions, secret: AGENT_SECRET },
      { timeout: 15_000 }
    );
    return res.json(response.data);
  } catch (err) {
    return res.status(502).json({ error: 'Agent did not respond', detail: err.message });
  }
});

export default router;
export const getAgentState = () => agentState;
