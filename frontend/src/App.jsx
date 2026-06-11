import { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { useSessions } from './hooks/useSessions';

const AUTH_TOKEN = 'demo_token';

export default function App() {
  const { sessions, currentId, create, switchTo, remove, updateTitle } = useSessions();
  const [chatHistory, setChatHistory] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  // 加载历史
  const loadHistory = useCallback(async (threadId) => {
    try {
      const res = await fetch(`/get_chat_history?thread_id=${threadId}`);
      const data = await res.json();
      setChatHistory(data.history || []);
    } catch {
      setChatHistory([]);
    }
  }, []);

  // 发送消息
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isStreaming) return;

    const userMsg = { role: 'user', content: text };
    setChatHistory(prev => [...prev, userMsg]);
    setIsStreaming(true);

    // 自动更新标题
    if (currentId) {
      const s = sessions.find(s => s.id === currentId);
      if (s && s.title.startsWith('新会话')) {
        updateTitle(currentId, text.length > 15 ? text.substring(0, 15) + '...' : text);
      }
    }

    // 创建 AI 消息占位
    const aiMsg = { role: 'assistant', content: '', isStreaming: true };
    setChatHistory(prev => [...prev, aiMsg]);

    try {
      const res = await fetch('/agentrun', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: text, token: AUTH_TOKEN, thread_id: currentId }),
      });

      if (!res.ok) {
        setChatHistory(prev => {
          const copy = [...prev];
          copy[copy.length - 1] = { role: 'assistant', content: `错误: ${res.status}`, isError: true };
          return copy;
        });
        setIsStreaming(false);
        return;
      }

      // 读 SSE 流
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6);
            if (dataStr === '[DONE]') break;
            try {
              const data = JSON.parse(dataStr);
              for (const key in data) {
                if (data[key]?.research_info) {
                  fullContent = data[key].research_info;
                  setChatHistory(prev => {
                    const copy = [...prev];
                    copy[copy.length - 1] = {
                      ...copy[copy.length - 1],
                      content: fullContent,
                      isStreaming: true,
                    };
                    return copy;
                  });
                }
              }
            } catch { /* 分片不完整，跳过 */ }
          }
        }
      }

      // 流结束
      setChatHistory(prev => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: 'assistant', content: fullContent };
        return copy;
      });
    } catch {
      setChatHistory(prev => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: 'assistant', content: '连接失败，请检查服务器。', isError: true };
        return copy;
      });
    } finally {
      setIsStreaming(false);
    }
  }, [currentId, isStreaming, sessions, updateTitle]);

  // 切换会话
  const handleSwitch = useCallback((id) => {
    switchTo(id);
    loadHistory(id);
  }, [switchTo, loadHistory]);

  // 新建会话
  const handleCreate = useCallback(() => {
    const id = create();
    setChatHistory([]);
    loadHistory(id);
  }, [create, loadHistory]);

  // 当前会话标题
  const currentTitle = sessions.find(s => s.id === currentId)?.title || 'AI 智能体协作平台';

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        sessions={sessions}
        currentId={currentId}
        onSwitch={handleSwitch}
        onCreate={handleCreate}
        onDelete={remove}
      />
      <ChatArea
        title={currentTitle}
        messages={chatHistory}
        isStreaming={isStreaming}
        onSend={sendMessage}
        welcomeMsg="👋 欢迎使用 AI 智能体协作平台！四 Agent 管线已就绪。试试问我：'迟到怎么惩罚？' 或 '写一个贪吃蛇游戏'"
      />
    </div>
  );
}
