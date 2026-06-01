import { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import MessageInput from './MessageInput';

export default function ChatArea({ title, messages, isStreaming, onSend, welcomeMsg }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <section className="flex-1 flex flex-col justify-between bg-gray-900 relative">
      {/* 顶部标题栏 */}
      <header className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🧠</span>
          <div>
            <h1 className="text-base font-bold tracking-wide">{title}</h1>
            <p className="text-xs text-gray-400">四 Agent 协作管线 — 规划 → 调研 → 编码 → 审查</p>
          </div>
        </div>
        <div className="text-xs text-blue-400 bg-blue-400/10 border border-blue-400/20 px-3 py-1 rounded-full flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          运行中
        </div>
      </header>

      {/* 消息区 */}
      <main
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col gap-6 w-full max-w-4xl mx-auto scroll-smooth"
      >
        {messages.length === 0 ? (
          <div className="flex gap-4">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex-shrink-0 flex items-center justify-center text-sm">AI</div>
            <div className="bg-gray-800 p-4 rounded-xl rounded-tl-none border border-gray-800 text-sm text-gray-200 shadow-sm">
              {welcomeMsg}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} isStreaming={msg.isStreaming} isError={msg.isError} />
          ))
        )}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
          <ChatMessage role="assistant" content="" isStreaming={true} />
        )}
      </main>

      {/* 输入区 */}
      <MessageInput onSend={onSend} disabled={isStreaming} />
    </section>
  );
}
