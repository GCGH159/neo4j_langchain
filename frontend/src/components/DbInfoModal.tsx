import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { X, Database, Loader2 } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
}

interface DbStats {
  labels: string[];
  relationship_types: string[];
  node_counts: Record<string, number>;
  total_relationships: number;
}

export const DbInfoModal: React.FC<Props> = ({ open, onClose }) => {
  const [stats, setStats] = useState<DbStats | null>(null);
  const [schema, setSchema] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'stats' | 'schema'>('stats');

  useEffect(() => {
    if (open) {
      setLoading(true);
      Promise.all([api.getDbStats(), api.getDbSchema()])
        .then(([s, sc]) => {
          setStats(s);
          setSchema(sc.schema);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-500" />
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">数据库信息</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tab 切换 */}
        <div className="flex px-6 pt-3 gap-1">
          {(['stats', 'schema'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${
                activeTab === tab
                  ? 'bg-gray-100 dark:bg-gray-800 text-emerald-600 font-medium'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'stats' ? '📊 统计' : '📋 Schema'}
            </button>
          ))}
        </div>

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            </div>
          ) : activeTab === 'stats' && stats ? (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">节点标签</h4>
                <div className="flex flex-wrap gap-2">
                  {stats.labels.map((label) => (
                    <span
                      key={label}
                      className="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm"
                    >
                      {label}: {stats.node_counts[label] || 0}
                    </span>
                  ))}
                  {stats.labels.length === 0 && (
                    <span className="text-gray-400 text-sm">暂无节点</span>
                  )}
                </div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">关系类型</h4>
                <div className="flex flex-wrap gap-2">
                  {stats.relationship_types.map((rt) => (
                    <span
                      key={rt}
                      className="px-3 py-1 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm"
                    >
                      {rt}
                    </span>
                  ))}
                  {stats.relationship_types.length === 0 && (
                    <span className="text-gray-400 text-sm">暂无关系</span>
                  )}
                </div>
              </div>
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <span className="text-sm text-gray-500">
                  总关系数：
                  <span className="font-mono text-emerald-600">{stats.total_relationships}</span>
                </span>
              </div>
            </div>
          ) : activeTab === 'schema' ? (
            <pre className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 text-xs font-mono text-gray-700 dark:text-gray-300 overflow-x-auto whitespace-pre-wrap">
              {schema || '暂无 Schema 信息'}
            </pre>
          ) : null}
        </div>
      </div>
    </div>
  );
};
