import React, { useState } from 'react';
import { Session } from '../types';
import { Plus, MessageSquare, Trash2, Database, Activity } from 'lucide-react';

interface Props {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  onShowDbInfo: () => void;
  dbConnected: boolean;
}

export const Sidebar: React.FC<Props> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onShowDbInfo,
  dbConnected,
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="w-72 bg-gray-900 text-gray-100 flex flex-col h-full">
      {/* 头部 */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center gap-2 mb-3">
          <Database className="w-5 h-5 text-emerald-400" />
          <h1 className="text-lg font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
            Neo4j Chat
          </h1>
        </div>
        <button
          onClick={onCreateSession}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          新建会话
        </button>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto py-2">
        {sessions.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500 text-sm">
            暂无会话，点击上方按钮创建
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`group mx-2 mb-0.5 px-3 py-2.5 rounded-lg cursor-pointer flex items-center gap-2 transition-colors ${
                activeSessionId === session.id
                  ? 'bg-gray-700 text-white'
                  : 'hover:bg-gray-800 text-gray-300'
              }`}
              onClick={() => onSelectSession(session.id)}
              onMouseEnter={() => setHoveredId(session.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0 text-gray-400" />
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate">{session.name}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {new Date(session.updated_at).toLocaleDateString('zh-CN', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              </div>
              {hoveredId === session.id && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  className="flex-shrink-0 p-1 hover:bg-red-600 rounded transition-colors"
                  title="删除会话"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* 底部状态栏 */}
      <div className="p-3 border-t border-gray-700">
        <button
          onClick={onShowDbInfo}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm text-gray-400"
        >
          <Activity className="w-4 h-4" />
          <span>数据库状态</span>
          <span
            className={`ml-auto w-2 h-2 rounded-full ${
              dbConnected ? 'bg-emerald-400' : 'bg-red-400'
            }`}
          />
        </button>
      </div>
    </div>
  );
};
