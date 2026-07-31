/**
 * Admin Dashboard page with stats, auction management, and create auction form.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { StatusBadge, formatPrice } from '../components/AuctionCard';
import api from '../services/api';

export default function AdminDashboardPage() {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [stats, setStats] = useState(null);
  const [auctions, setAuctions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!isAdmin) {
      navigate('/');
      return;
    }
    loadDashboard();
  }, [isAdmin]);

  async function loadDashboard() {
    try {
      const [statsData, auctionsData, usersData] = await Promise.all([
        api.getDashboardStats(),
        api.getAuctions({ page_size: 50 }),
        api.getUsers(),
      ]);
      setStats(statsData);
      setAuctions(auctionsData?.results || []);
      setUsers(usersData?.results || usersData || []);
    } catch (e) {
      console.error('Failed to load dashboard:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCancelAuction(auctionId) {
    if (!confirm('Cancel this auction?')) return;
    try {
      await api.cancelAuction(auctionId);
      toast.success('Auction cancelled');
      loadDashboard();
    } catch (e) {
      toast.error(e.message || 'Failed to cancel');
    }
  }

  if (loading) {
    return <div className="page"><div className="loading-page"><div className="spinner"></div></div></div>;
  }

  return (
    <div className="page">
      <div className="container">
        <div className="section-header">
          <h1 className="section-header__title">Admin Dashboard</h1>
          <p className="section-header__subtitle">Manage auctions and monitor platform activity</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="stats-grid" id="admin-stats">
            <div className="stat-card stat-card--orange">
              <div className="stat-card__label">Active Auctions</div>
              <div className="stat-card__value">{stats.active_auctions}</div>
            </div>
            <div className="stat-card stat-card--blue">
              <div className="stat-card__label">Total Auctions</div>
              <div className="stat-card__value">{stats.total_auctions}</div>
            </div>
            <div className="stat-card stat-card--green">
              <div className="stat-card__label">Total Revenue</div>
              <div className="stat-card__value">{formatPrice(stats.total_revenue)}</div>
            </div>
            <div className="stat-card stat-card--purple">
              <div className="stat-card__label">Total Users</div>
              <div className="stat-card__value">{stats.total_users}</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="filter-chips" style={{ marginBottom: 'var(--space-xl)' }}>
          <button className={`filter-chip ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
            Auctions
          </button>
          <button className={`filter-chip ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
            Users
          </button>
          <button className={`filter-chip ${activeTab === 'create' ? 'active' : ''}`} onClick={() => setActiveTab('create')}>
            + Create Auction
          </button>
        </div>

        {/* Auctions Table */}
        {activeTab === 'overview' && (
          <div className="card">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" id="auctions-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Current Price</th>
                    <th>Bids</th>
                    <th>Ends</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {auctions.map(auction => (
                    <tr key={auction.id}>
                      <td>
                        <a onClick={() => navigate(`/auctions/${auction.id}`)} style={{ cursor: 'pointer' }}>
                          {auction.title}
                        </a>
                      </td>
                      <td><StatusBadge status={auction.status} /></td>
                      <td style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                        {formatPrice(auction.current_price)}
                      </td>
                      <td>{auction.bid_count}</td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(auction.end_time).toLocaleString()}
                      </td>
                      <td>
                        {['ACTIVE', 'SCHEDULED'].includes(auction.status) && (
                          <button
                            className="btn btn--ghost btn--sm"
                            onClick={() => handleCancelAuction(auction.id)}
                            style={{ color: 'var(--error)' }}
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Users Table */}
        {activeTab === 'users' && (
          <div className="card">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" id="users-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Bids</th>
                    <th>Won</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {(Array.isArray(users) ? users : []).map(u => (
                    <tr key={u.id}>
                      <td style={{ fontWeight: 500 }}>{u.display_name || u.username}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                      <td>
                        <span className={`badge badge--${u.role === 'ADMIN' ? 'active' : 'scheduled'}`}>
                          {u.role}
                        </span>
                      </td>
                      <td>{u.total_bids || 0}</td>
                      <td>{u.auctions_won || 0}</td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Create Auction Form */}
        {activeTab === 'create' && <CreateAuctionForm onSuccess={() => { setActiveTab('overview'); loadDashboard(); }} />}
      </div>
    </div>
  );
}


function CreateAuctionForm({ onSuccess }) {
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    start_price: '',
    min_increment: '1000',
    start_time: '',
    end_time: '',
    bike_make: '',
    bike_model: '',
    bike_year: new Date().getFullYear(),
    bike_mileage: '',
    bike_engine_cc: '',
    bike_fuel_type: 'PETROL',
    bike_color: '',
    bike_condition: 'GOOD',
    bike_description: '',
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createAuction({
        ...form,
        start_price: parseFloat(form.start_price),
        min_increment: parseFloat(form.min_increment),
        bike_year: parseInt(form.bike_year),
        bike_mileage: parseInt(form.bike_mileage),
        bike_engine_cc: parseInt(form.bike_engine_cc),
      });
      toast.success('Auction created successfully!');
      onSuccess();
    } catch (e) {
      toast.error(e.message || 'Failed to create auction');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card__header">
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Create New Auction</h2>
      </div>
      <div className="card__body">
        <form onSubmit={handleSubmit} id="create-auction-form">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 'var(--space-md)', color: 'var(--accent-primary)' }}>
            Auction Details
          </h3>

          <div className="form-group">
            <label className="form-label">Title</label>
            <input type="text" name="title" className="form-input" value={form.title} onChange={handleChange} required placeholder="e.g., 2023 Royal Enfield Classic 350 - Low Mileage" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label className="form-label">Start Price (₹)</label>
              <input type="number" name="start_price" className="form-input" value={form.start_price} onChange={handleChange} required min="0" />
            </div>
            <div className="form-group">
              <label className="form-label">Min Increment (₹)</label>
              <input type="number" name="min_increment" className="form-input" value={form.min_increment} onChange={handleChange} required min="100" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label className="form-label">Start Time</label>
              <input type="datetime-local" name="start_time" className="form-input" value={form.start_time} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">End Time</label>
              <input type="datetime-local" name="end_time" className="form-input" value={form.end_time} onChange={handleChange} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea name="description" className="form-input" rows="3" value={form.description} onChange={handleChange} placeholder="Auction description..." style={{ resize: 'vertical' }} />
          </div>

          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 'var(--space-md)', marginTop: 'var(--space-xl)', color: 'var(--accent-primary)' }}>
            Bike Specifications
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label className="form-label">Make</label>
              <input type="text" name="bike_make" className="form-input" value={form.bike_make} onChange={handleChange} required placeholder="Royal Enfield" />
            </div>
            <div className="form-group">
              <label className="form-label">Model</label>
              <input type="text" name="bike_model" className="form-input" value={form.bike_model} onChange={handleChange} required placeholder="Classic 350" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label className="form-label">Year</label>
              <input type="number" name="bike_year" className="form-input" value={form.bike_year} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label className="form-label">Engine CC</label>
              <input type="number" name="bike_engine_cc" className="form-input" value={form.bike_engine_cc} onChange={handleChange} required placeholder="349" />
            </div>
            <div className="form-group">
              <label className="form-label">Mileage (km)</label>
              <input type="number" name="bike_mileage" className="form-input" value={form.bike_mileage} onChange={handleChange} required placeholder="12000" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label className="form-label">Color</label>
              <input type="text" name="bike_color" className="form-input" value={form.bike_color} onChange={handleChange} required placeholder="Black" />
            </div>
            <div className="form-group">
              <label className="form-label">Fuel Type</label>
              <select name="bike_fuel_type" className="form-select" value={form.bike_fuel_type} onChange={handleChange}>
                <option value="PETROL">Petrol</option>
                <option value="DIESEL">Diesel</option>
                <option value="ELECTRIC">Electric</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Condition</label>
              <select name="bike_condition" className="form-select" value={form.bike_condition} onChange={handleChange}>
                <option value="EXCELLENT">Excellent</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
              </select>
            </div>
          </div>

          <button type="submit" className="btn btn--primary btn--lg" disabled={loading} style={{ marginTop: 'var(--space-lg)' }}>
            {loading ? 'Creating...' : 'Create Auction'}
          </button>
        </form>
      </div>
    </div>
  );
}
