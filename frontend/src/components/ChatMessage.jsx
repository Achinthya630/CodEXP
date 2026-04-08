import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot, FileCode2, Copy, Check } from 'lucide-react';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const [copiedText, setCopiedText] = React.useState('');

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(''), 2000);
  };

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} py-4`}>
      <div className={`flex max-w-[85%] sm:max-w-[75%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-lg mt-1 ${
          isUser 
            ? 'bg-gradient-to-br from-indigo-400 to-purple-500 ml-3 shrink-0' 
            : 'bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-600 mr-3 shrink-0'
        }`}>
          {isUser ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-indigo-300" />}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-5 pt-3 pb-4 rounded-2xl ${
            isUser 
              ? 'bg-[var(--color-codex-user-msg)] text-indigo-50 rounded-tr-sm shadow-sm' 
              : 'bg-[var(--color-codex-ai-msg)] border border-[var(--color-codex-border)] text-slate-200 rounded-tl-sm shadow-md'
          }`}>
            {message.isTyping && !message.content ? (
              <div className="flex space-x-1.5 h-6 items-center px-1">
                <div className="w-2 h-2 bg-indigo-400 rounded-full typing-dot"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full typing-dot"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full typing-dot"></div>
              </div>
            ) : (
              <div className="prose prose-invert prose-p:leading-relaxed prose-pre:m-0 max-w-none text-[15px]">
                <ReactMarkdown
                  components={{
                    pre({ node, inline, className, children, ...props }) {
                      const text = String(children.props.children).replace(/\n$/, '');
                      return (
                        <div className="relative group mt-3 mb-4 rounded-lg overflow-hidden border border-[var(--color-codex-border)]">
                          <div className="flex items-center justify-between px-4 py-2 bg-[#0b0f19] border-b border-[var(--color-codex-border)]">
                            <span className="text-xs text-slate-400 font-mono">code</span>
                            <button
                              onClick={() => handleCopy(text)}
                              className="text-slate-400 hover:text-white transition-colors"
                            >
                              {copiedText === text ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                            </button>
                          </div>
                          <pre className="p-4 overflow-x-auto bg-[#0b0f19]" {...props}>
                            {children}
                          </pre>
                        </div>
                      );
                    },
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return inline ? (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      )
                    }
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Referenced Files (only for AI) */}
          {message.referencedFiles && message.referencedFiles.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5 pl-2 max-w-full">
              {message.referencedFiles.map((file, i) => (
                <div key={i} className="flex items-center text-[10px] px-2 py-1 rounded bg-[var(--color-codex-bg)] border border-[var(--color-codex-border)] text-[var(--color-codex-muted)] hover:text-indigo-300 hover:border-indigo-500/30 transition-colors cursor-default max-w-full truncate">
                  <FileCode2 className="w-3 h-3 mr-1 flex-shrink-0" />
                  <span className="truncate">{file.split('/').pop()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
