/**
 * API service for communicating with the Django backend.
 * Handles JWT token management and request/response interceptors.
 */

const API_BASE = '/api';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE;
  }

  getToken() {
    return localStorage.getItem('access_token');
  }

  setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle token refresh on 401
      if (response.status === 401 && !options._retry) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          return this.request(endpoint, { ...options, _retry: true });
        }
        this.clearTokens();
        window.location.href = '/login';
        return null;
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const error = new Error(data?.message || data?.detail || `Request failed: ${response.status}`);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (error) {
      if (error.status) throw error;
      throw new Error('Network error. Please check your connection.');
    }
  }

  async refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setTokens(data.access, data.refresh || refresh);
        return true;
      }
    } catch (e) {
      // Refresh failed
    }
    return false;
  }

  // ─── Auth ─────────────────────────────────────────────────

  async register(userData) {
    const data = await this.request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    if (data?.tokens) {
      this.setTokens(data.tokens.access, data.tokens.refresh);
      localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  }

  async login(email, password) {
    const data = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (data?.access) {
      this.setTokens(data.access, data.refresh);
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }
    }
    return data;
  }

  async getProfile() {
    return this.request('/auth/me/');
  }

  async updateProfile(data) {
    return this.request('/auth/me/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // ─── Auctions ─────────────────────────────────────────────

  async getAuctions(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.append(key, value);
      }
    });
    const queryStr = query.toString();
    return this.request(`/auctions/${queryStr ? `?${queryStr}` : ''}`);
  }

  async getAuction(id) {
    return this.request(`/auctions/${id}/`);
  }

  async createAuction(data) {
    return this.request('/auctions/admin/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async cancelAuction(id) {
    return this.request(`/auctions/admin/${id}/cancel/`, {
      method: 'POST',
    });
  }

  // ─── Bids ─────────────────────────────────────────────────

  async getBids(auctionId) {
    return this.request(`/auctions/${auctionId}/bids/`);
  }

  async placeBid(auctionId, amount) {
    return this.request(`/auctions/${auctionId}/bids/`, {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
  }

  async getMyBids() {
    return this.request('/auctions/my-bids/');
  }

  // ─── Admin ────────────────────────────────────────────────

  async getDashboardStats() {
    return this.request('/auth/dashboard/');
  }

  async getUsers() {
    return this.request('/auth/users/');
  }

  // ─── Health ───────────────────────────────────────────────

  async healthCheck() {
    return this.request('/health/');
  }
}

export const api = new ApiService();
export default api;
