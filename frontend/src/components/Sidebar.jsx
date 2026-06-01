export default function Sidebar({ sessions, currentId, onSwitch, onCreate, onDelete }) {
  return (
    <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col justify-between flex-shrink-0">
      <div className="p-3 flex flex-col gap-4 overflow-hidden h-full">
        <button
          onClick={onCreate}
          className="w-full border border-gray-700 hover:border-blue-500 hover:bg-gray-900 text-sm font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95"
        >
          <span>+</span> 新建会话
        </button>
        <div className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1">
          {sessions.map(s => {
            const isActive = s.id === currentId;
            return (
              <button
                key={s.id}
                onClick={() => onSwitch(s.id)}
                className={`w-full text-left text-sm py-3 px-4 rounded-xl flex items-center justify-between transition-all group ${
                  isActive
                    ? 'bg-gray-800 text-blue-400 font-medium border border-gray-700'
                    : 'text-gray-400 hover:bg-gray-900/50 hover:text-gray-200'
                }`}
              >
                <span className="flex items-center gap-2 truncate flex-1">
                  <span>💬</span>
                  <span className="truncate">{s.title}</span>
                </span>
                <span
                  onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                  className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 px-1 transition-all"
                >
                  ×
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="p-4 border-t border-gray-800 bg-gray-950/50 text-xs text-gray-500 text-center">
        🧠 AI 智能体协作平台
      </div>
    </aside>
  );
}
