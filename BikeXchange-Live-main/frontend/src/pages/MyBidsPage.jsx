/**
 * My Bids page - shows the authenticated user's bid history.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function MyBidsPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    loadBids();
  }, [isAuthenticated]);

  async function loadBids() {
    try {
      const data = await api.getMyBids();
      setBids(data?.results || data || []);
    } catch (e) {
      console.error('Failed to load bids:', e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="page"><div className="loading-page"><div className="spinner"></div></div></div>;
  }

  return (
    <div className="page">
      <div className="container">
        <div className="section-header">
          <h1 className="section-header__title">My Bids</h1>
          <p className="section-header__subtitle">
            Your bidding history across all auctions
          </p>
        </div>

        {bids.length > 0 ? (
          <div className="card">
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table" id="my-bids-table">
                <thead>
                  <tr>
                    <th>Auction</th>
                    <th>Amount</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {(Array.isArray(bids) ? bids : []).map((bid, idx) => (
                    <tr key={bid.id || idx}>
                      <td style={{ fontWeight: 500 }}>
                        {bid.auction?.title || 'Auction'}
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                        ₹{parseFloat(bid.amount).toLocaleString('en-IN')}
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {new Date(bid.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state__icon">🎯</div>
            <h3 className="empty-state__title">No Bids Yet</h3>
            <p className="empty-state__text">
              You haven't placed any bids. Browse live auctions and start bidding!
            </p>
            <button onClick={() => navigate('/auctions')} className="btn btn--primary" style={{ marginTop: 'var(--space-lg)' }}>
              Browse Auctions
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
