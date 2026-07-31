/**
 * WebSocket service for real-time auction bidding.
 * Manages connection lifecycle and message handling.
 */

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnect = 5;
    this.reconnectDelay = 2000;
    this.auctionId = null;
  }

  connect(auctionId) {
    this.auctionId = auctionId;
    const token = localStorage.getItem('access_token');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/auctions/${auctionId}/${token ? `?token=${token}` : ''}`;

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log(`[WS] Connected to auction ${auctionId}`);
      this.reconnectAttempts = 0;
      this.emit('connected', { auctionId });
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit(data.type, data);
      } catch (e) {
        console.error('[WS] Failed to parse message:', e);
      }
    };

    this.socket.onclose = (event) => {
      console.log(`[WS] Disconnected (code: ${event.code})`);
      this.emit('disconnected', { code: event.code });

      // Auto-reconnect if not intentional close
      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnect) {
        this.reconnectAttempts++;
        console.log(`[WS] Reconnecting attempt ${this.reconnectAttempts}/${this.maxReconnect}...`);
        setTimeout(() => this.connect(auctionId), this.reconnectDelay * this.reconnectAttempts);
      }
    };

    this.socket.onerror = (error) => {
      console.error('[WS] Error:', error);
      this.emit('error', { error });
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.listeners.clear();
    this.reconnectAttempts = this.maxReconnect; // Prevent auto-reconnect
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('[WS] Cannot send - not connected');
    }
  }

  placeBid(amount) {
    this.send({
      type: 'place_bid',
      amount: parseFloat(amount),
    });
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      if (callbacks) {
        const idx = callbacks.indexOf(callback);
        if (idx !== -1) callbacks.splice(idx, 1);
      }
    };
  }

  off(event) {
    this.listeners.delete(event);
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => cb(data));
  }

  get isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const wsService = new WebSocketService();
export default wsService;
