/**
 * Auction card component for grid listings.
 * Shows bike thumbnail, title, price, countdown, and bid count.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const BIKE_EMOJIS = {
  'Royal Enfield': '🏍️',
  'KTM': '🏎️',
  'Bajaj': '🏍️',
  'Honda': '🏍️',
  'Yamaha': '🏍️',
  'Kawasaki': '🏍️',
  'TVS': '🏍️',
  'Suzuki': '🏍️',
  'Husqvarna': '🏍️',
};

function formatPrice(price) {
  const num = parseFloat(price);
  if (num >= 100000) {
    return `₹${(num / 100000).toFixed(2)}L`;
  }
  return `₹${num.toLocaleString('en-IN')}`;
}

function formatTime(seconds) {
  if (seconds <= 0) return 'Ended';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function StatusBadge({ status }) {
  const statusClass = status.toLowerCase();
  return (
    <span className={`badge badge--${statusClass}`}>
      {status}
    </span>
  );
}

export default function AuctionCard({ auction }) {
  const navigate = useNavigate();
  const [timeLeft, setTimeLeft] = useState(auction.time_remaining || 0);

  useEffect(() => {
    if (auction.status !== 'ACTIVE') return;

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
  }, [auction.status]);

  const bike = auction.bike;
  const emoji = BIKE_EMOJIS[bike?.make] || '🏍️';

  return (
    <div
      className="auction-card"
      onClick={() => navigate(`/auctions/${auction.id}`)}
      id={`auction-card-${auction.id}`}
    >
      <div className="auction-card__image">
        {bike?.images && bike.images.length > 0 && bike.images[0].startsWith('http') ? (
          <img 
            src={bike.images[0]} 
            alt={auction.title} 
            loading="lazy"
            decoding="async"
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <span className="auction-card__image-placeholder">{emoji}</span>
        )}
        <div className="auction-card__status">
          <StatusBadge status={auction.status} />
        </div>
      </div>

      <div className="auction-card__body">
        <h3 className="auction-card__title">{auction.title}</h3>

        {bike && (
          <div className="auction-card__bike-info">
            <span>{bike.year}</span>
            <span>•</span>
            <span>{bike.engine_cc} CC</span>
            <span>•</span>
            <span>{bike.mileage?.toLocaleString()} km</span>
          </div>
        )}

        <div className="auction-card__price-row">
          <div>
            <div className="auction-card__price-label">
              {auction.status === 'COMPLETED' ? 'Final Price' : 'Current Bid'}
            </div>
            <div className="auction-card__price">
              {formatPrice(auction.current_price)}
            </div>
          </div>

          <div className="auction-card__countdown">
            {auction.status === 'ACTIVE' && (
              <>
                <div className="auction-card__time">{formatTime(timeLeft)}</div>
                <div className="auction-card__bids">{auction.bid_count} bids</div>
              </>
            )}
            {auction.status === 'SCHEDULED' && (
              <div className="auction-card__bids">Starting soon</div>
            )}
            {auction.status === 'COMPLETED' && (
              <div className="auction-card__bids">{auction.bid_count} bids</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export { StatusBadge, formatPrice, formatTime };
