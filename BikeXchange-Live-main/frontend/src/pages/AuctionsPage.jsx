/**
 * Auctions listing page with filtering, search, and sorting.
 */

import { useState, useEffect } from 'react';
import AuctionCard from '../components/AuctionCard';
import api from '../services/api';

const STATUS_FILTERS = [
  { label: 'All', value: '' },
  { label: 'Live', value: 'ACTIVE' },
  { label: 'Upcoming', value: 'SCHEDULED' },
  { label: 'Completed', value: 'COMPLETED' },
];

export default function AuctionsPage() {
  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadAuctions();
  }, [statusFilter, search]);

  async function loadAuctions() {
    setLoading(true);
    try {
      const params = { page_size: 24 };
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;

      const data = await api.getAuctions(params);
      setAuctions(data?.results || []);
      setTotalCount(data?.count || 0);
    } catch (e) {
      console.error('Failed to load auctions:', e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="container">
        <div className="section-header">
          <h1 className="section-header__title">Motorcycle Auctions</h1>
          <p className="section-header__subtitle">
            {totalCount} auction{totalCount !== 1 ? 's' : ''} available
          </p>
        </div>

        {/* Filters */}
        <div className="filters-bar" id="auction-filters">
          <div className="filter-chips">
            {STATUS_FILTERS.map(filter => (
              <button
                key={filter.value}
                className={`filter-chip ${statusFilter === filter.value ? 'active' : ''}`}
                onClick={() => setStatusFilter(filter.value)}
              >
                {filter.label}
              </button>
            ))}
          </div>

          <input
            type="text"
            className="search-input"
            placeholder="Search by make, model, or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            id="auction-search"
          />
        </div>

        {/* Auction Grid */}
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
            <div className="empty-state__icon">🔍</div>
            <h3 className="empty-state__title">No Auctions Found</h3>
            <p className="empty-state__text">
              {search
                ? `No auctions match "${search}". Try a different search.`
                : 'No auctions available in this category right now.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
