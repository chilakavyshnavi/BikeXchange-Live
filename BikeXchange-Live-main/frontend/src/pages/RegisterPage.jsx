/**
 * Registration page with full form validation.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export default function RegisterPage() {
  const { register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    phone: '',
    password: '',
    password_confirm: '',
  });
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

    // Client-side validation
    if (form.password !== form.password_confirm) {
      setErrors({ password_confirm: 'Passwords do not match.' });
      setLoading(false);
      return;
    }

    if (form.password.length < 8) {
      setErrors({ password: 'Password must be at least 8 characters.' });
      setLoading(false);
      return;
    }

    try {
      await register(form);
      toast.success('Account created successfully!');
      navigate('/auctions');
    } catch (err) {
      const details = err.data?.details || {};
      setErrors(details);
      toast.error(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card" id="register-card" style={{ maxWidth: '500px' }}>
        <div className="auth-card__logo">Vutto</div>
        <p className="auth-card__subtitle">Create your account to start bidding</p>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="reg-first-name">First Name</label>
              <input
                id="reg-first-name"
                type="text"
                name="first_name"
                className={`form-input ${errors.first_name ? 'form-input--error' : ''}`}
                placeholder="Rahul"
                value={form.first_name}
                onChange={handleChange}
                required
              />
              {errors.first_name && <p className="form-error">{errors.first_name}</p>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="reg-last-name">Last Name</label>
              <input
                id="reg-last-name"
                type="text"
                name="last_name"
                className={`form-input ${errors.last_name ? 'form-input--error' : ''}`}
                placeholder="Mehta"
                value={form.last_name}
                onChange={handleChange}
                required
              />
              {errors.last_name && <p className="form-error">{errors.last_name}</p>}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
              type="email"
              name="email"
              className={`form-input ${errors.email ? 'form-input--error' : ''}`}
              placeholder="you@example.com"
              value={form.email}
              onChange={handleChange}
              required
            />
            {errors.email && <p className="form-error">{errors.email}</p>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-username">Username</label>
            <input
              id="reg-username"
              type="text"
              name="username"
              className={`form-input ${errors.username ? 'form-input--error' : ''}`}
              placeholder="rahul_m"
              value={form.username}
              onChange={handleChange}
              required
            />
            {errors.username && <p className="form-error">{errors.username}</p>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-phone">Phone (optional)</label>
            <input
              id="reg-phone"
              type="tel"
              name="phone"
              className="form-input"
              placeholder="+91-9876543210"
              value={form.phone}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              type="password"
              name="password"
              className={`form-input ${errors.password ? 'form-input--error' : ''}`}
              placeholder="Min 8 characters"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
            />
            {errors.password && <p className="form-error">{Array.isArray(errors.password) ? errors.password.join(' ') : errors.password}</p>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-password-confirm">Confirm Password</label>
            <input
              id="reg-password-confirm"
              type="password"
              name="password_confirm"
              className={`form-input ${errors.password_confirm ? 'form-input--error' : ''}`}
              placeholder="Repeat password"
              value={form.password_confirm}
              onChange={handleChange}
              required
            />
            {errors.password_confirm && <p className="form-error">{errors.password_confirm}</p>}
          </div>

          <button
            type="submit"
            className="btn btn--primary btn--full btn--lg"
            disabled={loading}
            id="register-submit-btn"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="auth-card__footer">
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
