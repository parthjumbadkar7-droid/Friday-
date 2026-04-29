import { useState, useCallback } from 'react';
import { getHistory, saveHistory, deleteHistory } from '../utils/api';

export function useHistory() {
  const [history, setHistory] = useState([]);
  const [loaded, setLoaded] = useState(false);

  const loadHistory = useCallback(async () => {
    try {
      const data = await getHistory();
      setHistory(data);
      setLoaded(true);
      return data;
    } catch (err) {
      console.warn('[useHistory] Failed to load:', err.message);
      setLoaded(true);
      return [];
    }
  }, []);

  const saveConversation = useCallback(async (conversation) => {
    try {
      await saveHistory(conversation);
      setHistory((prev) => {
        const idx = prev.findIndex((c) => c.id === conversation.id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = conversation;
          return next;
        }
        return [...prev, conversation];
      });
    } catch (err) {
      console.warn('[useHistory] Failed to save:', err.message);
    }
  }, []);

  const removeConversation = useCallback(async (id) => {
    try {
      await deleteHistory(id);
      setHistory((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.warn('[useHistory] Failed to delete:', err.message);
    }
  }, []);

  return { history, loaded, loadHistory, saveConversation, removeConversation };
}
