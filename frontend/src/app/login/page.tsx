'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { loginApi, checkDbStatusApi, DbStatusResponse } from '@/services/authApi';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [dbStatus, setDbStatus] = useState<DbStatusResponse | null>(null);

  useEffect(() => {
    // Check backend and DB status on mount
    checkDbStatusApi().then((res) => setDbStatus(res)).catch(() => {});
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!username.trim() || !password) {
      setError('Please provide both username and password.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await loginApi({
        username: username.trim(),
        password,
      });

      setSuccessMsg(`Welcome back, ${res.user.username}! Redirecting...`);
      setTimeout(() => {
        router.push('/');
      }, 900);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#eef2f7',
        backgroundImage: 'radial-gradient(circle at 50% 20%, #ffffff 0%, #eef2f7 75%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {/* Top Bar with Brand and DB Indicator */}
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
        }}
      >
        {/* Database Status Badge */}
        {dbStatus && (
          <div
            title={dbStatus.message || 'Database status'}
            style={{
              fontSize: '11px',
              fontWeight: '700',
              padding: '6px 12px',
              borderRadius: '20px',
              backgroundColor: dbStatus.status === 'connected' ? '#ecfdf5' : '#fef2f2',
              color: dbStatus.status === 'connected' ? '#047857' : '#b91c1c',
              border: `1px solid ${dbStatus.status === 'connected' ? '#a7f3d0' : '#fecaca'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: dbStatus.status === 'connected' ? '#10b981' : '#ef4444',
                display: 'inline-block',
              }}
            />
            <span>
              {dbStatus.status === 'connected'
                ? `DB: ${dbStatus.dialect?.toUpperCase() || 'MONGODB'}`
                : 'DB Offline'}
            </span>
          </div>
        )}
      </div>

      {/* Main Login Card - Styled matching the classic Lesson Plan Generator box */}
      <div
        style={{
          backgroundColor: '#ffffff',
          padding: '32px 28px',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
          width: '100%',
          maxWidth: '520px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: '22px',
        }}
      >
        {/* Panel Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f1f5f9',
            paddingBottom: '16px',
          }}
        >
          <div>
            <h2
              style={{
                fontSize: '20px',
                fontWeight: '800',
                color: '#0f172a',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                margin: 0,
              }}
            >
              <span
                style={{
                  backgroundColor: '#eef2ff',
                  color: '#4f46e5',
                  padding: '6px 10px',
                  borderRadius: '10px',
                  fontSize: '18px',
                }}
              >
                🔐
              </span>
              <span>Account Login</span>
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '6px 0 0 0' }}>
              Enter your credentials to manage and generate NIE curriculum lesson plans
            </p>
          </div>
        </div>

        {/* Success Alert */}
        {successMsg && (
          <div
            style={{
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '13px',
              color: '#15803d',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>✓</span>
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div
            style={{
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '10px',
              padding: '12px 14px',
              fontSize: '13px',
              color: '#b91c1c',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Detail Box 1: Username / Identity Box */}
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <label
              htmlFor="login-username"
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: '700',
                textTransform: 'uppercase',
                color: '#334155',
                letterSpacing: '0.05em',
              }}
            >
              Username or Email
            </label>
            <input
              id="login-username"
              type="text"
              required
              disabled={isLoading}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. teacher_john or user@school.lk"
              style={{
                width: '100%',
                padding: '11px 14px',
                backgroundColor: '#ffffff',
                border: '1.5px solid #cbd5e1',
                borderRadius: '9px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#1e293b',
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.15s ease',
              }}
              onFocus={(e) => (e.target.style.borderColor = '#4f46e5')}
              onBlur={(e) => (e.target.style.borderColor = '#cbd5e1')}
            />
          </div>

          {/* Detail Box 2: Password Box */}
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label
                htmlFor="login-password"
                style={{
                  display: 'block',
                  fontSize: '12px',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  color: '#334155',
                  letterSpacing: '0.05em',
                }}
              >
                Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6366f1',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              required
              disabled={isLoading}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              style={{
                width: '100%',
                padding: '11px 14px',
                backgroundColor: '#ffffff',
                border: '1.5px solid #cbd5e1',
                borderRadius: '9px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#1e293b',
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.15s ease',
              }}
              onFocus={(e) => (e.target.style.borderColor = '#4f46e5')}
              onBlur={(e) => (e.target.style.borderColor = '#cbd5e1')}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '6px',
              backgroundColor: isLoading ? '#94a3b8' : '#4f46e5',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              padding: '13px 20px',
              fontSize: '15px',
              fontWeight: '700',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 10px rgba(79, 70, 229, 0.25)',
              transition: 'background-color 0.15s ease, transform 0.1s ease',
            }}
            onMouseEnter={(e) => {
              if (!isLoading) (e.currentTarget.style.backgroundColor = '#4338ca');
            }}
            onMouseLeave={(e) => {
              if (!isLoading) (e.currentTarget.style.backgroundColor = '#4f46e5');
            }}
          >
            {isLoading ? (
              <>
                <span
                  style={{
                    display: 'inline-block',
                    width: '14px',
                    height: '14px',
                    border: '2px solid #ffffff',
                    borderTopColor: 'transparent',
                    borderRadius: '50%',
                    animation: 'spin 0.7s linear infinite',
                  }}
                />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <span>→</span>
              </>
            )}
          </button>
        </form>

        {/* Footer Link to Signup */}
        <div
          style={{
            borderTop: '1px solid #f1f5f9',
            paddingTop: '16px',
            textAlign: 'center',
            fontSize: '13px',
            color: '#64748b',
          }}
        >
          Don&apos;t have an account yet?{' '}
          <Link
            href="/signup"
            style={{
              color: '#4f46e5',
              fontWeight: '700',
              textDecoration: 'none',
            }}
          >
            Create an Account
          </Link>
        </div>
      </div>
    </div>
  );
}
