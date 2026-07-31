/**
 * Navigation bar component with auth-aware menu items.
 */

import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'active' : '';

  // Don't show navbar on auth pages
  if (['/login', '/register'].includes(location.pathname)) return null;

  return (
    <nav className="navbar" id="main-navbar">
      <div className="container">
        <Link to="/" className="navbar__logo">Vutto</Link>

        <ul className="navbar__links">
          <li>
            <Link to="/" className={`navbar__link ${isActive('/')}`}>Home</Link>
          </li>
          <li>
            <Link to="/auctions" className={`navbar__link ${isActive('/auctions')}`}>Auctions</Link>
          </li>
          {isAuthenticated && (
            <li>
              <Link to="/my-bids" className={`navbar__link ${isActive('/my-bids')}`}>My Bids</Link>
            </li>
          )}
          {isAdmin && (
            <li>
              <Link to="/admin" className={`navbar__link ${isActive('/admin')}`}>Dashboard</Link>
            </li>
          )}
        </ul>

        <div className="navbar__actions">
          {isAuthenticated ? (
            <>
              <div className="navbar__user">
                <div className="navbar__avatar">
                  {user?.first_name?.[0]?.toUpperCase() || 'U'}
                </div>
                <span>{user?.display_name || user?.username}</span>
              </div>
              <button onClick={logout} className="btn btn--ghost btn--sm" id="logout-btn">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn--ghost btn--sm">Login</Link>
              <Link to="/register" className="btn btn--primary btn--sm">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
