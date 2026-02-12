import { useState, useEffect, useCallback } from 'react';
import type { Session, Message } from './types';
import { api } from './api';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { DbInfoModal } from './components/DbInfoModal';

function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showDbInfo, setShowDbInfo] = useState(false);
  const [dbConnected, setDbConnected] = useState(false);

  // 初始化：获取健康状态和会话列表
  useEffect(() => {
    api.getHealth()
      .then((h) => setDbConnected(h.neo4j))
      .catch(() => setDbConnected(false));

    api.listSessions()
      .then(setSessions)
      .catch(console.error);
  }, []);

  // 切换会话时加载消息历史
  useEffect(() => {
    if (activeSessionId) {
      api.getSessionMessages(activeSessionId)
        .then(setMessages)
        .catch(() => setMessages([]));
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  const handleCreateSession = useCallback(async () => {
    try {
      const session = await api.createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
    } catch (e) {
      console.error('创建会话失败:', e);
    }
  }, []);

  const handleDeleteSession = useCallback(async (id: string) => {
    try {
      await api.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error('删除会话失败:', e);
    }
  }, [activeSessionId]);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const handleSessionNameUpdate = useCallback((name: string) => {
    if (!activeSessionId) return;
    setSessions((prev) =>
      prev.map((s) => (s.id === activeSessionId ? { ...s, name } : s))
    );
    api.renameSession(activeSessionId, name).catch(console.error);
  }, [activeSessionId]);

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        onShowDbInfo={() => setShowDbInfo(true)}
        dbConnected={dbConnected}
      />
      <ChatArea
        sessionId={activeSessionId}
        sessionName={activeSession?.name || '新会话'}
        messages={messages}
        setMessages={setMessages}
        onSessionNameUpdate={handleSessionNameUpdate}
      />
      <DbInfoModal open={showDbInfo} onClose={() => setShowDbInfo(false)} />
    </div>
  );
}

export default App;
