'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="login-wrapper">
        <div className="loading-container">
          <div className="spinner" />
          <p className="loading-text">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="login-wrapper">
      <div className="login-card glass-card-static animate-in">
        <div className="login-logo">
          <span className="login-logo-icon">🚦</span>
          <h1>Smart City Traffic<br />Optimisation System</h1>
          <p>AI-powered traffic management platform</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && <div className="login-error">⚠️ {error}</div>}

          <div>
            <label className="input-label" htmlFor="email-input">Email Address</label>
            <input
              id="email-input"
              type="email"
              className="input-field"
              placeholder="admin@smartcity.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label className="input-label" htmlFor="password-input">Password</label>
            <input
              id="password-input"
              type="password"
              className="input-field"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            id="login-btn"
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: '100%', marginTop: 8 }}
          >
            {loading ? '⏳ Signing in...' : '🔐 Sign In'}
          </button>
        </form>

        <div className="login-help">
          <p style={{ marginTop: 16 }}>Demo credentials:</p>
          <p><strong>admin@smartcity.com</strong> / Admin@123</p>
          <p><strong>officer@smartcity.com</strong> / Officer@123</p>
        </div>
      </div>
    </div>
  );
}
