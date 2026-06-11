import { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

function renderMarkdown(text) {
  if (!text) return '';
  return DOMPurify.sanitize(marked.parse(text));
}

// DP: 流式打字机效果 — 首帧3字，之后2字/50ms（有可见的逐字输出感）
function useTypewriter(text, isStreaming) {
  const [displayed, setDisplayed] = useState('');
  const timerRef = useRef(null);
  const firstFrame = useRef(true);

  useEffect(() => {
    if (!text) { setDisplayed(''); return; }
    if (!isStreaming) { setDisplayed(text); return; }

    let idx = displayed.length;
    firstFrame.current = idx === 0;

    timerRef.current = setInterval(() => {
      if (idx >= text.length) {
        clearInterval(timerRef.current);
        return;
      }
      idx += firstFrame.current ? 3 : 2;     // 首帧3字，之后每帧2字
      firstFrame.current = false;
      if (idx > text.length) idx = text.length;
      setDisplayed(text.substring(0, idx));
    }, 50);                                     // 每50ms一帧

    return () => clearInterval(timerRef.current);
  }, [text, isStreaming]);

  // 清理
  useEffect(() => () => clearInterval(timerRef.current), []);

  return displayed;
}

export default function ChatMessage({ role, content, isStreaming, isError }) {
  const displayed = useTypewriter(content, isStreaming);
  const isUser = role === 'user';

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-sm shadow-md ${
        isUser ? 'bg-indigo-500' : 'bg-blue-600'
      }`}>
        {isUser ? '我' : 'AI'}
      </div>
      <div className={`p-4 rounded-xl text-sm max-w-[85%] w-full shadow-sm break-words ${
        isUser
          ? 'bg-indigo-600 rounded-tr-none text-white max-w-[75%]'
          : isError
            ? 'bg-red-900/50 border border-red-800 rounded-tl-none text-red-200'
            : 'bg-gray-800 rounded-tl-none border border-gray-800 text-gray-200'
      }`}>
        {isUser ? (
          content
        ) : (
          <div
            className={`markdown-body ${isStreaming && displayed !== content ? 'typing-cursor' : ''}`}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(displayed) }}
          />
        )}
        {!isUser && isStreaming && !displayed && (
          <span className="typing-cursor text-gray-400">思考中...</span>
        )}
      </div>
    </div>
  );
}
