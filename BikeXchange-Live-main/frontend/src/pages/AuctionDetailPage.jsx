/**
 * Auction detail page with real-time bidding panel.
 * Features live countdown, WebSocket bid updates, bid history, and bike specs.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { StatusBadge, formatPrice, formatTime } from '../components/AuctionCard';
import api from '../services/api';
import wsService from '../services/websocket';

export default function AuctionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const toast = useToast();

  const [auction, setAuction] = useState(null);
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bidAmount, setBidAmount] = useState('');
  const [bidding, setBidding] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);
  const bidListRef = useRef(null);

  // Load auction data
  useEffect(() => {
    loadAuction();
    return () => {
      wsService.disconnect();
    };
  }, [id]);

  // WebSocket setup
  useEffect(() => {
    if (!auction) return;

    wsService.connect(id);

    const unsubs = [
      wsService.on('connected', () => setWsConnected(true)),
      wsService.on('disconnected', () => setWsConnected(false)),
      wsService.on('bid_placed', (data) => {
        const newBid = data.bid;
        setBids(prev => [newBid, ...prev]);
        setAuction(prev => ({
          ...prev,
          current_price: data.current_price,
          bid_count: (prev.bid_count || 0) + 1,
        }));

        // Show toast for bids
        if (user && newBid.bidder?.id === user.id) {
          toast.success(`Bid of ₹${parseFloat(newBid.amount).toLocaleString('en-IN')} placed successfully!`);
        } else if (user && newBid.bidder?.id !== user.id) {
          toast.info(`${newBid.bidder?.display_name || 'Someone'} bid ₹${parseFloat(newBid.amount).toLocaleString('en-IN')}`);
        }
      }),
      wsService.on('auction_update', (data) => {
        setAuction(prev => ({
          ...prev,
          status: data.status,
          time_remaining: data.time_remaining,
          winner: data.winner,
          current_price: data.current_price || prev.current_price,
        }));

        if (data.status === 'COMPLETED') {
          if (data.winner?.id === user?.id) {
            toast.success('🎉 Congratulations! You won this auction!');
          } else {
            toast.info('This auction has ended.');
          }
        } else if (data.status === 'ACTIVE') {
          toast.info('This auction is now live!');
        }
      }),
      wsService.on('error', (data) => {
        toast.error(data.message || 'WebSocket error');
      }),
    ];

    return () => unsubs.forEach(fn => fn());
  }, [auction?.id]);

  // Countdown timer
  useEffect(() => {
    if (!auction || auction.status !== 'ACTIVE') return;

    setTimeLeft(auction.time_remaining || 0);

    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 0) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [auction?.id, auction?.status, auction?.time_remaining]);

  // Update default bid amount when current price changes
  useEffect(() => {
    if (auction) {
      const minNext = parseFloat(auction.current_price) + parseFloat(auction.min_increment);
      // Only auto-update if current input is empty or lower than the new minimum
      if (!bidAmount || parseFloat(bidAmount) < minNext) {
        setBidAmount(minNext.toString());
      }
    }
  }, [auction?.current_price]);

  async function loadAuction() {
    try {
      const data = await api.getAuction(id);
      setAuction(data);
      setBids(data.bids || []);
      setTimeLeft(data.time_remaining || 0);
    } catch (e) {
      toast.error('Auction not found');
      navigate('/auctions');
    } finally {
      setLoading(false);
    }
  }

  async function handlePlaceBid(amount) {
    if (!isAuthenticated) {
      toast.warning('Please login to place a bid');
      navigate('/login');
      return;
    }

    const bidVal = parseFloat(amount || bidAmount);
    if (isNaN(bidVal) || bidVal <= 0) {
      toast.error('Enter a valid bid amount');
      return;
    }

    setBidding(true);
    try {
      // Use WebSocket if connected, else fall back to REST
      if (wsService.isConnected) {
        wsService.placeBid(bidVal);
        // Success toast and input update will be handled by the 'bid_placed' event listener
        setTimeout(() => setBidding(false), 1000); // Prevent spamming
      } else {
        const bid = await api.placeBid(id, bidVal);
        setBids(prev => [bid, ...prev]);
        setAuction(prev => ({
          ...prev,
          current_price: bid.amount,
          bid_count: (prev.bid_count || 0) + 1,
        }));
        toast.success(`Bid of ₹${bidVal.toLocaleString('en-IN')} placed successfully!`);
        
        // Update bid input to next minimum for REST fallback
        const nextMin = bidVal + parseFloat(auction.min_increment);
        setBidAmount(nextMin.toString());
        setBidding(false);
      }
    } catch (err) {
      toast.error(err.message || 'Failed to place bid');
      setBidding(false);
    }
  }

  function handleQuickBid(increment) {
    const current = parseFloat(auction.current_price);
    const amount = current + increment;
    setBidAmount(amount.toString());
    handlePlaceBid(amount);
  }

  function formatTimerDisplay(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  if (loading) {
    return <div className="page"><div className="loading-page"><div className="spinner"></div></div></div>;
  }

  if (!auction) return null;

  const bike = auction.bike;
  const minNextBid = parseFloat(auction.current_price) + parseFloat(auction.min_increment);
  const canBid = auction.status === 'ACTIVE' && isAuthenticated && auction.seller?.id !== user?.id;

  return (
    <div className="page">
      <div className="container">
        {/* Back button */}
        <button onClick={() => navigate('/auctions')} className="btn btn--ghost" style={{ marginBottom: 'var(--space-lg)' }}>
          ← Back to Auctions
        </button>

        <div className="auction-detail" id="auction-detail">
          {/* Left Column: Bike Info */}
          <div>
            <div className="auction-detail__gallery">
              {bike?.images && bike.images.length > 0 && bike.images[0].startsWith('http') ? (
                <img 
                  src={bike.images[0]} 
                  alt={auction.title} 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <span className="auction-detail__placeholder">🏍️</span>
              )}
              <div style={{ position: 'absolute', top: 'var(--space-md)', right: 'var(--space-md)' }}>
                <StatusBadge status={auction.status} />
              </div>
            </div>

            <div className="auction-detail__info">
              <h1 className="auction-detail__title">{auction.title}</h1>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                {auction.description || bike?.description}
              </p>

              {/* Bike Specifications */}
              {bike && (
                <div className="auction-detail__specs">
                  <div className="spec-item">
                    <div className="spec-item__label">Make</div>
                    <div className="spec-item__value">{bike.make}</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Model</div>
                    <div className="spec-item__value">{bike.model}</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Year</div>
                    <div className="spec-item__value">{bike.year}</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Engine</div>
                    <div className="spec-item__value">{bike.engine_cc} CC</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Mileage</div>
                    <div className="spec-item__value">{bike.mileage?.toLocaleString()} km</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Fuel</div>
                    <div className="spec-item__value">{bike.fuel_type}</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Color</div>
                    <div className="spec-item__value">{bike.color}</div>
                  </div>
                  <div className="spec-item">
                    <div className="spec-item__label">Condition</div>
                    <div className="spec-item__value">{bike.condition}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Bid Panel */}
          <div className="bid-panel" id="bid-panel">
            <div className="bid-panel__header">
              <div className="bid-panel__status">
                <StatusBadge status={auction.status} />
                {wsConnected && (
                  <span style={{ fontSize: '0.72rem', color: 'var(--success)' }}>● Live</span>
                )}
              </div>
              <div className="bid-panel__price-label">Current Bid</div>
              <div className="bid-panel__price">
                ₹{parseFloat(auction.current_price).toLocaleString('en-IN')}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 'var(--space-xs)' }}>
                Starting: ₹{parseFloat(auction.start_price).toLocaleString('en-IN')} • {auction.bid_count} bids
              </div>
            </div>

            {/* Countdown */}
            {auction.status === 'ACTIVE' && (
              <div className="bid-panel__countdown">
                <div className={`bid-panel__timer ${timeLeft < 60 ? 'urgent' : ''}`}>
                  {formatTimerDisplay(timeLeft)}
                </div>
                <div className="bid-panel__timer-label">Time Remaining</div>
              </div>
            )}

            {auction.status === 'SCHEDULED' && (
              <div className="bid-panel__countdown">
                <div className="bid-panel__timer" style={{ color: 'var(--warning)' }}>
                  UPCOMING
                </div>
                <div className="bid-panel__timer-label">
                  Starts {new Date(auction.start_time).toLocaleString()}
                </div>
              </div>
            )}

            {auction.status === 'COMPLETED' && (
              <div className="bid-panel__countdown">
                <div className="bid-panel__timer" style={{ color: 'var(--text-muted)' }}>
                  ENDED
                </div>
                {auction.winner && (
                  <div className="bid-panel__timer-label">
                    Won by {auction.winner.display_name}
                  </div>
                )}
              </div>
            )}

            {/* Bid Input */}
            {canBid && (
              <div className="bid-panel__body">
                <div className="bid-panel__quick-bids">
                  <button
                    className="quick-bid-btn"
                    onClick={() => handleQuickBid(parseFloat(auction.min_increment))}
                    disabled={bidding || timeLeft <= 0}
                  >
                    +₹{parseFloat(auction.min_increment).toLocaleString('en-IN')}
                  </button>
                  <button
                    className="quick-bid-btn"
                    onClick={() => handleQuickBid(parseFloat(auction.min_increment) * 2)}
                    disabled={bidding || timeLeft <= 0}
                  >
                    +₹{(parseFloat(auction.min_increment) * 2).toLocaleString('en-IN')}
                  </button>
                  <button
                    className="quick-bid-btn"
                    onClick={() => handleQuickBid(parseFloat(auction.min_increment) * 5)}
                    disabled={bidding || timeLeft <= 0}
                  >
                    +₹{(parseFloat(auction.min_increment) * 5).toLocaleString('en-IN')}
                  </button>
                </div>

                <div className="bid-input-group">
                  <input
                    type="number"
                    className="form-input"
                    value={bidAmount}
                    onChange={(e) => setBidAmount(e.target.value)}
                    min={minNextBid}
                    step={parseFloat(auction.min_increment)}
                    placeholder={`Min ₹${minNextBid.toLocaleString('en-IN')}`}
                    id="bid-amount-input"
                  />
                  <button
                    className="btn btn--primary"
                    onClick={() => handlePlaceBid()}
                    disabled={bidding || timeLeft <= 0}
                    id="place-bid-btn"
                  >
                    {bidding ? '...' : 'Bid'}
                  </button>
                </div>

                <div className="bid-panel__info">
                  Min increment: ₹{parseFloat(auction.min_increment).toLocaleString('en-IN')}
                </div>
              </div>
            )}

            {!isAuthenticated && auction.status === 'ACTIVE' && (
              <div className="bid-panel__body" style={{ textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-md)' }}>
                  Login to place bids
                </p>
                <button onClick={() => navigate('/login')} className="btn btn--primary btn--full">
                  Sign In to Bid
                </button>
              </div>
            )}

            {/* Bid History */}
            <div className="bid-history" ref={bidListRef}>
              <div className="bid-history__title">Bid History ({bids.length})</div>
              {bids.length > 0 ? (
                bids.map((bid, idx) => (
                  <div key={bid.id || idx} className="bid-item" style={idx === 0 ? { animation: 'bid-flash 1s ease' } : {}}>
                    <div>
                      <div className="bid-item__user">
                        {bid.bidder?.display_name || bid.bidder?.username || 'Anonymous'}
                      </div>
                      <div className="bid-item__time">
                        {new Date(bid.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="bid-item__amount">
                      ₹{parseFloat(bid.amount).toLocaleString('en-IN')}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 'var(--space-lg)' }}>
                  No bids yet. Be the first!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
