/**
 * Home page with hero section and featured auctions.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuctionCard from '../components/AuctionCard';
import api from '../services/api';

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [auctions, setAuctions] = useState([]);
  const [stats, setStats] = useState({ active: 0, total: 0, bids: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const data = await api.getAuctions({ status: 'ACTIVE', page_size: 6 });
      setAuctions(data?.results || []);

      // Calculate quick stats
      const allData = await api.getAuctions({ page_size: 1 });
      setStats({
        active: data?.count || 0,
        total: allData?.count || 0,
        bids: (data?.results || []).reduce((sum, a) => sum + (a.bid_count || 0), 0),
      });
    } catch (e) {
      console.error('Failed to load auctions:', e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* ─── Hero Section ─── */}
      <section className="hero" id="hero-section">
        <div className="container hero__grid">
          <div className="hero__content">
            <div className="hero__badge">
              🏍️ Live Auctions Available Now
            </div>

            <h1 className="hero__title">
              Bid on Premium<br />
              <span>Used Motorcycles</span>
            </h1>

            <p className="hero__description">
              Join India's most exciting bike auction platform. Discover incredible
              deals on well-maintained motorcycles from top brands — Royal Enfield,
              KTM, Yamaha, and more.
            </p>

            <div className="hero__actions">
              <Link to="/auctions" className="btn btn--primary btn--lg" id="browse-auctions-btn">
                Browse Live Auctions
              </Link>
              {!isAuthenticated && (
                <Link to="/register" className="btn btn--secondary btn--lg">
                  Create Account
                </Link>
              )}
            </div>

            <div className="hero__stats">
              <div>
                <div className="hero__stat-value">{stats.active}+</div>
                <div className="hero__stat-label">Live Auctions</div>
              </div>
              <div>
                <div className="hero__stat-value">{stats.total}+</div>
                <div className="hero__stat-label">Total Auctions</div>
              </div>
              <div>
                <div className="hero__stat-value">{stats.bids}+</div>
                <div className="hero__stat-label">Active Bids</div>
              </div>
            </div>
          </div>
          
          <div className="hero__visual">
            <div className="hero__image-wrapper">
              <img 
                src="https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=1200&q=80" 
                alt="Premium Motorcycle" 
                className="hero__image"
              />
              <div className="hero__image-glow"></div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section className="how-it-works">
        <div className="container">
          <div className="section-header text-center">
            <h2 className="section-header__title">How It Works</h2>
            <p className="section-header__subtitle">Your dream bike in 3 simple steps</p>
          </div>
          <div className="steps-grid">
            <div className="step-card">
              <div className="step-card__icon">🔍</div>
              <h3 className="step-card__title">1. Browse & Inspect</h3>
              <p className="step-card__text">View high-res photos and detailed specifications of verified motorcycles.</p>
            </div>
            <div className="step-card">
              <div className="step-card__icon">⚡</div>
              <h3 className="step-card__title">2. Place Live Bids</h3>
              <p className="step-card__text">Join our real-time auction room and outbid others for the best price.</p>
            </div>
            <div className="step-card">
              <div className="step-card__icon">🏆</div>
              <h3 className="step-card__title">3. Win & Ride</h3>
              <p className="step-card__text">Secure the highest bid before the timer runs out and take your bike home.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Top Brands ─── */}
      <section className="brands-section">
        <div className="container">
          <p className="brands-title">FEATURING TOP BRANDS</p>
          <div className="brands-grid">
            <div className="brand-pill">Royal Enfield</div>
            <div className="brand-pill">KTM</div>
            <div className="brand-pill">Kawasaki</div>
            <div className="brand-pill">Yamaha</div>
            <div className="brand-pill">Honda</div>
            <div className="brand-pill">Bajaj</div>
          </div>
        </div>
      </section>

      {/* ─── Featured Auctions ─── */}
      <section className="page" style={{ paddingTop: 'var(--space-2xl)' }}>
        <div className="container">
          <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div>
              <h2 className="section-header__title">🔥 Live Auctions</h2>
              <p className="section-header__subtitle">
                Bid now on these active motorcycle auctions
              </p>
            </div>
            <Link to="/auctions" className="btn btn--outline btn--sm">View All →</Link>
          </div>

          {loading ? (
            <div className="loading-page"><div className="spinner"></div></div>
          ) : auctions.length > 0 ? (
            <div className="auction-grid">
              {auctions.map(auction => (
                <AuctionCard key={auction.id} auction={auction} />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state__icon">🏍️</div>
              <h3 className="empty-state__title">No Live Auctions</h3>
              <p className="empty-state__text">
                Check back soon! New auctions are added regularly.
              </p>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
