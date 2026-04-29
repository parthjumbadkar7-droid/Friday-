import { useEffect, useRef, useCallback } from 'react';
import { sendProactive } from '../utils/api';

const INACTIVITY_MS = 5 * 60 * 1000; // 5 minutes

export function useProactive(onProactiveMessage) {
  const timerRef = useRef(null);

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      try {
        const data = await sendProactive(5);
        if (data.reply) onProactiveMessage(data.reply);
      } catch (err) {
        console.warn('[useProactive] Failed:', err.message);
      }
    }, INACTIVITY_MS);
  }, [onProactiveMessage]);

  useEffect(() => {
    resetTimer();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [resetTimer]);

  return { resetTimer };
}
