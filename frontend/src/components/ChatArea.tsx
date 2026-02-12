import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import { api } from '../api';
import { MessageBubble } from './MessageBubble';
import { Send, Loader2, Sparkles } from 'lucide-react';

interface Props {
  sessionId: string | null;
  sessionName: string;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  onSessionNameUpdate: (name: string) => void;
}

export const ChatArea: React.FC<Props> = ({
  sessionId,
  sessionName,
  messages,
  setMessages,
  onSessionNameUpdate,
}) => {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 自动调整 textarea 高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim() || !sessionId || isStreaming) return;

    const userMessage = input.trim();
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    // 添加用户消息
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    // 如果是第一条消息，更新会话名称
    if (messages.length === 0) {
      onSessionNameUpdate(userMessage.slice(0, 30) + (userMessage.length > 30 ? '...' : ''));
    }

    // 添加空的 AI 消息占位
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
    setIsStreaming(true);

    await api.chatStream(
      sessionId,
      userMessage,
      (chunk) => {
        if (chunk.type === 'content') {
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg.role === 'assistant') {
              lastMsg.content += chunk.content;
            }
            return [...newMessages];
          });
        } else if (chunk.type === 'done') {
          setIsStreaming(false);
        } else if (chunk.type === 'error') {
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg.role === 'assistant') {
              lastMsg.content = `❌ ${chunk.content}`;
            }
            return [...newMessages];
          });
          setIsStreaming(false);
        }
      },
      (error) => {
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMsg = newMessages[newMessages.length - 1];
          if (lastMsg.role === 'assistant') {
            lastMsg.content = `❌ 网络错误: ${error.message}`;
          }
          return [...newMessages];
        });
        setIsStreaming(false);
      },
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 无会话选中的欢迎页
  if (!sessionId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-white dark:bg-gray-950 text-gray-400">
        <Sparkles className="w-16 h-16 mb-4 text-emerald-400 opacity-50" />
        <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">
          Neo4j 智能笔记助手
        </h2>
        <p className="text-sm text-gray-400 max-w-md text-center leading-relaxed">
          基于知识图谱的智能对话系统。
          <br />
          支持笔记管理、实体关系分析、自然语言查询。
          <br />
          点击左侧「新建会话」开始对话。
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-950">
      {/* 顶部标题 */}
      <div className="h-14 px-6 flex items-center border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm">
        <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
          {sessionName}
        </h2>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Sparkles className="w-10 h-10 mb-3 text-emerald-400 opacity-40" />
            <p className="text-sm">发送消息开始对话</p>
            <div className="mt-4 grid grid-cols-2 gap-2 max-w-lg">
              {[
                '记录：今天学习了 LangChain 框架',
                '查询关于 Python 的笔记',
                '查看数据库中有哪些实体',
                '分析当前图谱状态',
              ].map((hint, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInput(hint);
                    textareaRef.current?.focus();
                  }}
                  className="text-xs text-left px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-500 transition-colors"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <MessageBubble key={idx} message={msg} />
            ))}
            {isStreaming && messages[messages.length - 1]?.content === '' && (
              <div className="flex gap-3 px-4 py-3">
                <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center flex-shrink-0">
                  <Loader2 className="w-4 h-4 text-white animate-spin" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-2.5">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-4 bg-white dark:bg-gray-950">
        <div className="max-w-3xl mx-auto flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              disabled={isStreaming}
              rows={1}
              className="w-full resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-50 transition-shadow"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="flex-shrink-0 w-11 h-11 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {isStreaming ? (
              <Loader2 className="w-5 h-5 text-white animate-spin" />
            ) : (
              <Send className="w-5 h-5 text-white" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
