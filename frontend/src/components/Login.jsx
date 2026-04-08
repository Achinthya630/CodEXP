import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Code2 } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

function Login() {
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSuccess = async (credentialResponse) => {
    try {
      const res = await fetch(`${API_BASE_URL}/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });
      if (!res.ok) throw new Error('Authentication failed on server.');
      
      const data = await res.json();
      login(data.access_token, data.user);
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-codex-bg)] text-[var(--color-codex-text)] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-[#111827]/80 backdrop-blur-xl border border-[var(--color-codex-border)] rounded-3xl p-8 shadow-2xl shadow-black/50 text-center">
        <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-indigo-500/20 transform rotate-3 hover:rotate-12 transition-transform duration-300">
          <Code2 className="w-10 h-10 text-white" />
        </div>
        
        <h1 className="text-3xl font-bold mb-2 tracking-tight">Welcome to CodEx</h1>
        <p className="text-slate-400 mb-8 text-sm">
          Sign in to access your personal AI coding assistant and isolated repositories.
        </p>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-sm p-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="flex justify-center mb-4">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => setError('Google Login Failed')}
            theme="filled_black"
            shape="pill"
          />
        </div>
        
        <p className="text-xs text-slate-500 mt-6">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}

export default Login;
