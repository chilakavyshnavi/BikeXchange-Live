/**
 * Login page with email/password authentication.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export default function LoginPage() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      await login(form.email, form.password);
      toast.success('Welcome back!');
      navigate('/auctions');
    } catch (err) {
      const message = err.message || 'Login failed';
      if (message.includes('credentials') || message.includes('No active account')) {
        setErrors({ general: 'Invalid email or password.' });
      } else {
        setErrors({ general: message });
      }
      toast.error('Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card" id="login-card">
        <div className="auth-card__logo">Vutto</div>
        <p className="auth-card__subtitle">Sign in to your account</p>

        <form onSubmit={handleSubmit}>
          {errors.general && (
            <div style={{
              padding: 'var(--space-md)',
              background: 'var(--error-bg)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--error)',
              fontSize: '0.85rem',
              marginBottom: 'var(--space-lg)',
            }}>
              {errors.general}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              name="email"
              className={`form-input ${errors.email ? 'form-input--error' : ''}`}
              placeholder="you@example.com"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              name="password"
              className="form-input"
              placeholder="Your password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn--primary btn--full btn--lg"
            disabled={loading}
            id="login-submit-btn"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-card__footer">
          Don't have an account?{' '}
          <Link to="/register">Create one</Link>
        </div>
      </div>
    </div>
  );
}
