import React, { useState, useEffect } from 'react';
import { Database, Plus, Search, Folder, Zap, GitBranch, ChevronRight, Loader2, CircleCheck, AlertCircle } from 'lucide-react';
import { ingestRepo } from '../api';

export default function Sidebar({ repos, selectedRepo, onSelectRepo, onRepoIngested }) {
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestUrl, setIngestUrl] = useState('');
  const [ingestStatus, setIngestStatus] = useState({ type: '', msg: '' });

  const handleIngest = async (e) => {
    e.preventDefault();
    if (!ingestUrl.trim()) return;

    setIsIngesting(true);
    setIngestStatus({ type: 'info', msg: 'Ingesting repository... This may take a while.' });
    
    try {
      const data = await ingestRepo(ingestUrl);
      setIngestStatus({ type: 'success', msg: `Successfully ingested ${data.files_processed} files!` });
      onRepoIngested(data.repo_name);
      setIngestUrl('');
      // Clear success msg after 3s
      setTimeout(() => setIngestStatus({ type: '', msg: '' }), 3000);
    } catch (err) {
      setIngestStatus({ type: 'error', msg: err.message || 'Failed to ingest' });
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="w-72 sm:w-80 h-screen flex flex-col bg-[var(--color-codex-sidebar)] border-r border-[var(--color-codex-border)] flex-shrink-0 z-10 transition-all duration-300">
      {/* Brand Header */}
      <div className="p-5 border-b border-[var(--color-codex-border)] flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-purple-200">
          CodEXP
        </h1>
      </div>

      {/* Ingestion Widget */}
      <div className="p-4 border-b border-[var(--color-codex-border)]">
        <h2 className="text-xs font-semibold text-[var(--color-codex-muted)] uppercase tracking-wider mb-3 flex items-center">
          <Database className="w-3.5 h-3.5 mr-1.5" />
          Add Repository
        </h2>
        <form onSubmit={handleIngest} className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-400 transition-colors">
            <GitBranch className="w-4 h-4" />
          </div>
          <input
            type="text"
            className="w-full pl-9 pr-10 py-2.5 bg-[var(--color-codex-bg)] border border-[var(--color-codex-border)] rounded-lg text-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 placeholder-slate-500"
            placeholder="https://github.com/..."
            value={ingestUrl}
            onChange={(e) => setIngestUrl(e.target.value)}
            disabled={isIngesting}
          />
          <button
            type="submit"
            disabled={isIngesting || !ingestUrl.trim()}
            className="absolute inset-y-0 right-0 pr-2 flex items-center disabled:opacity-50"
          >
            {isIngesting ? (
              <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
            ) : (
              <Plus className="w-5 h-5 text-slate-400 hover:text-indigo-400 transition-colors" />
            )}
          </button>
        </form>
        
        {/* Status Toast/Message */}
        {ingestStatus.msg && (
          <div className={`mt-3 text-xs flex items-start space-x-1.5 p-2.5 rounded-md ${
            ingestStatus.type === 'error' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
            ingestStatus.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
            'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          }`}>
            {ingestStatus.type === 'error' && <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />}
            {ingestStatus.type === 'success' && <CircleCheck className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />}
            {ingestStatus.type === 'info' && <Loader2 className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 animate-spin" />}
            <span className="leading-relaxed">{ingestStatus.msg}</span>
          </div>
        )}
      </div>

      {/* Repo List */}
      <div className="flex-1 overflow-y-auto p-3">
        <h2 className="px-2 text-xs font-semibold text-[var(--color-codex-muted)] uppercase tracking-wider mb-2 flex items-center">
          <Folder className="w-3.5 h-3.5 mr-1.5" />
          Ingested Repos
        </h2>
        {repos.length === 0 ? (
          <div className="p-3 text-sm text-[var(--color-codex-muted)] text-center py-8">
            <div className="w-12 h-12 rounded-full bg-[var(--color-codex-border)] flex items-center justify-center mx-auto mb-3 opacity-50">
              <Search className="w-5 h-5" />
            </div>
            No repositories found.<br/>Add one to get started.
          </div>
        ) : (
          <div className="space-y-1">
            {repos.map((repo) => (
              <button
                key={repo.name}
                onClick={() => onSelectRepo(repo.name)}
                className={`w-full text-left p-3 rounded-lg flex items-center justify-between group transition-all duration-200 ${
                  selectedRepo === repo.name
                    ? 'bg-indigo-500/10 border border-indigo-500/30 shadow-sm'
                    : 'hover:bg-[var(--color-codex-bg)] border border-transparent hover:border-[var(--color-codex-border)]'
                }`}
              >
                <div className="flex flex-col truncate pr-2">
                  <span className={`text-sm font-medium truncate ${selectedRepo === repo.name ? 'text-indigo-300' : 'text-slate-300 group-hover:text-white'}`}>
                    {repo.name.split('/').pop()}
                  </span>
                  <span className="text-xs text-[var(--color-codex-muted)] truncate">
                    {repo.name.split('/')[0]}
                  </span>
                </div>
                <div className={`flex flex-col items-end ${selectedRepo === repo.name ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                  <ChevronRight className={`w-4 h-4 ${selectedRepo === repo.name ? 'text-indigo-400' : 'text-slate-500'}`} />
                  <span className="text-[10px] text-slate-500 mt-1" title={`${repo.chunks} chunks stored`}>
                    {repo.chunks} c
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
