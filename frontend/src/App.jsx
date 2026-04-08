import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatInput from './components/ChatInput';
import ChatMessage from './components/ChatMessage';
import Login from './components/Login';
import { getRepos, createQueryStream } from './api';
import { useAuth } from './context/AuthContext';
import { Code2, MessagesSquare, LogOut } from 'lucide-react';

function MainApp() {
  const [repos, setRepos] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState('');
  const [messages, setMessages] = useState({}); // { repoName: [msg1, msg2] }
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);
  const { user, logout } = useAuth();

  // Load repos on mount
  useEffect(() => {
    fetchRepos();
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, selectedRepo]);

  const fetchRepos = async () => {
    try {
      const data = await getRepos();
      setRepos(data.repos);
      // Auto-select first if none selected
      if (data.repos.length > 0 && !selectedRepo) {
        setSelectedRepo(data.repos[0].name);
      }
    } catch (err) {
      console.error("Failed to load repos:", err);
    }
  };

  const handleRepoIngested = (repoName) => {
    fetchRepos();
    setSelectedRepo(repoName);
  };

  const currentMessages = selectedRepo ? (messages[selectedRepo] || []) : [];

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || !selectedRepo || isStreaming) return;

    const userQuestion = inputValue;
    setInputValue('');
    
    // Add User Message
    const newMessages = [
      ...currentMessages,
      { role: 'user', content: userQuestion, id: Date.now().toString() }
    ];
    
    setMessages(prev => ({ ...prev, [selectedRepo]: newMessages }));
    setIsStreaming(true);

    // Add empty AI message container for streaming
    const aiMessageId = (Date.now() + 1).toString();
    setMessages(prev => ({
      ...prev,
      [selectedRepo]: [...newMessages, { 
        role: 'ai', 
        content: '', 
        id: aiMessageId,
        isTyping: true,
        referencedFiles: []
      }]
    }));

    try {
      await createQueryStream(
        userQuestion,
        selectedRepo,
        // onChunk
        (chunk) => {
          setMessages(prev => {
            const repoMsgs = prev[selectedRepo] || [];
            return {
              ...prev,
              [selectedRepo]: repoMsgs.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, content: msg.content + chunk, isTyping: false } 
                  : msg
              )
            };
          });
        },
        // onDone
        (metadata) => {
          setMessages(prev => {
            const repoMsgs = prev[selectedRepo] || [];
            return {
              ...prev,
              [selectedRepo]: repoMsgs.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, referencedFiles: metadata.referenced_files, isTyping: false } 
                  : msg
              )
            };
          });
          setIsStreaming(false);
        },
        // onError
        (error) => {
          console.error("Stream error:", error);
          setMessages(prev => {
            const repoMsgs = prev[selectedRepo] || [];
            return {
              ...prev,
              [selectedRepo]: repoMsgs.map(msg => 
                msg.id === aiMessageId 
                  ? { ...msg, content: msg.content + `\n\n**Error**: ${error.message}`, isTyping: false } 
                  : msg
              )
            };
          });
          setIsStreaming(false);
        }
      );
    } catch (err) {
      console.error("Failed to start stream:", err);
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-codex-bg)] text-[var(--color-codex-text)]">
      {/* Sidebar Overlay for Mobile could go here */}
      
      {/* Sidebar */}
      <Sidebar 
        repos={repos} 
        selectedRepo={selectedRepo} 
        onSelectRepo={setSelectedRepo}
        onRepoIngested={handleRepoIngested}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full max-w-full overflow-hidden">
        
        {/* Header (Mobile / Active Repo Indicator) */}
        <header className="h-14 border-b border-[var(--color-codex-border)] flex items-center px-4 shrink-0 bg-[var(--color-codex-bg)]/80 backdrop-blur-sm z-10">
          {selectedRepo ? (
            <div className="flex items-center text-sm font-medium text-slate-300">
              <Code2 className="w-4 h-4 mr-2 text-indigo-400" />
              {selectedRepo}
            </div>
          ) : (
            <div className="text-sm font-medium text-slate-500">Select a repository</div>
          )}
          
          {/* User Profile / Logout */}
          <div className="ml-auto flex items-center gap-4">
            <div className="text-sm text-slate-300 hidden sm:block">
              {user?.name}
            </div>
            {user?.picture && (
              <img src={user.picture} alt="Profile" className="w-8 h-8 rounded-full border border-[var(--color-codex-border)]" />
            )}
            <button 
              onClick={logout}
              className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors cursor-pointer"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Messages List Area */}
        <div className="flex-1 overflow-y-auto w-full">
          <div className="w-full max-w-4xl mx-auto p-4 sm:p-6 pb-32">
            {!selectedRepo ? (
              <div className="h-full flex flex-col items-center justify-center text-center mt-32">
                <div className="w-16 h-16 bg-[var(--color-codex-border)] rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-black/20">
                  <MessagesSquare className="w-8 h-8 text-indigo-400" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Welcome to CodEx</h2>
                <p className="text-[var(--color-codex-muted)] max-w-md">
                  Ingest a GitHub repository from the sidebar to start asking questions about its codebase.
                </p>
              </div>
            ) : currentMessages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center mt-32">
                <Code2 className="w-12 h-12 text-[var(--color-codex-border)] mb-4" />
                <h2 className="text-xl font-medium mb-1 border-b border-indigo-500/30 pb-1 text-slate-300">Ask about <span className="text-indigo-400 font-code">{selectedRepo.split('/').pop()}</span></h2>
                <p className="text-[var(--color-codex-muted)] text-sm max-w-sm mt-3">
                  Try asking "How does the authentication work?" or "Where are the API routes defined?"
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {currentMessages.map(msg => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
                {/* Spacer block to provide empty blank space at the bottom */}
                <div ref={messagesEndRef} className="h-24 shrink-0" />
              </div>
            )}
          </div>
        </div>

        {/* Input Area (Fixed to bottom, floating over content) */}
        <div className="absolute bottom-0 left-0 w-full z-20">
          <ChatInput 
            input={inputValue}
            setInput={setInputValue}
            onSubmit={handleSendMessage}
            isStreaming={isStreaming}
            disabled={!selectedRepo}
          />
        </div>
        
      </div>
    </div>
  );
}

function App() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
      <Route path="/*" element={user ? <MainApp /> : <Navigate to="/login" />} />
    </Routes>
  );
}

export default App;
