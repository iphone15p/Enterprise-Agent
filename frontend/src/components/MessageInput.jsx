import { useState, useRef } from 'react';

export default function MessageInput({ onSend, disabled }) {
  const [text, setText] = useState('');
  const inputRef = useRef(null);

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSend(text);
    setText('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <footer className="p-4 bg-gradient-to-t from-gray-900 via-gray-900 to-transparent">
      <div className="max-w-4xl mx-auto flex gap-3">
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="输入你的问题或任务..."
          autoComplete="off"
          className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-5 py-4 text-gray-100 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 transition-all placeholder-gray-500"
        />
        <button
          onClick={handleSend}
          disabled={disabled}
          className={`bg-blue-600 hover:bg-blue-500 text-white px-6 py-4 rounded-xl font-bold text-sm tracking-wider transition-all active:scale-95 flex items-center shadow-lg shadow-blue-600/20 ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          发送
        </button>
      </div>
    </footer>
  );
}
