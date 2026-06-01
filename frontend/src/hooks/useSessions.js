import { useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'ai_sessions';

function loadSessions() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

export function useSessions() {
  const [sessions, setSessions] = useState(loadSessions);
  const [currentId, setCurrentId] = useState(() => {
    const saved = loadSessions();
    return saved.length > 0 ? saved[0].id : '';
  });

  // 如果没有会话，自动创建一个
  useEffect(() => {
    if (sessions.length === 0) {
      const id = 'thread_' + Math.random().toString(36).substring(2, 9);
      const s = { id, title: '新会话 ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
      setSessions([s]);
      setCurrentId(id);
    }
  }, []);

  const create = useCallback(() => {
    const id = 'thread_' + Math.random().toString(36).substring(2, 9);
    const s = { id, title: '新会话 ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setSessions(prev => {
      const next = [s, ...prev];
      saveSessions(next);
      return next;
    });
    setCurrentId(id);
    return id;
  }, []);

  const switchTo = useCallback((id) => {
    setCurrentId(id);
  }, []);

  const remove = useCallback((id) => {
    setSessions(prev => {
      const next = prev.filter(s => s.id !== id);
      saveSessions(next);
      if (id === currentId && next.length > 0) {
        setCurrentId(next[0].id);
      }
      return next;
    });
  }, [currentId]);

  const updateTitle = useCallback((id, title) => {
    setSessions(prev => {
      const next = prev.map(s => s.id === id ? { ...s, title } : s);
      saveSessions(next);
      return next;
    });
  }, []);

  return { sessions, currentId, create, switchTo, remove, updateTitle };
}
