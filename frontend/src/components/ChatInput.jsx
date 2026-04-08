import React, { useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

export default function ChatInput({ input, setInput, onSubmit, isStreaming, disabled }) {
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  return (
    <form onSubmit={onSubmit} className="relative max-w-4xl w-full mx-auto p-4 sm:p-6 bg-gradient-to-t from-[var(--color-codex-bg)] via-[var(--color-codex-bg)] to-transparent pt-10">
      <div className="relative flex items-end glass rounded-2xl p-2 shadow-2xl transition-all focus-within:ring-2 focus-within:ring-indigo-500/50 focus-within:border-indigo-400/50">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isStreaming}
          placeholder={disabled ? "Select a repository to start asking questions..." : "Ask about the codebase..."}
          className="w-full max-h-[200px] bg-transparent text-[var(--color-codex-text)] resize-none py-2.5 pl-4 pr-12 focus:outline-none disabled:opacity-50 text-[15px] leading-relaxed"
          rows={1}
        />
        
        <button
          type="submit"
          disabled={!input.trim() || disabled || isStreaming}
          className={`absolute right-3 bottom-2.5 p-2 rounded-xl flex items-center justify-center transition-all duration-200 ${
            input.trim() && !disabled && !isStreaming
              ? 'bg-indigo-500 hover:bg-indigo-600 shadow-md shadow-indigo-500/20 text-white'
              : 'bg-slate-800 text-slate-500 opacity-50 cursor-not-allowed'
          }`}
        >
          {isStreaming ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4 -ml-0.5 mt-0.5" />
          )}
        </button>
      </div>
      <div className="text-center mt-2 text-[11px] text-[var(--color-codex-muted)]">
        CodEx uses RAG to fetch context. It may still make mistakes. Verify important information.
      </div>
    </form>
  );
}
