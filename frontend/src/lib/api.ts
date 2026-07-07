/**
 * API Client — Centralized HTTP client with token management.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiClient {
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  setTokens(access: string, refresh: string): void {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  private async refreshAccessToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      return true;
    } catch {
      return false;
    }
  }

  async fetch<T = any>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { skipAuth, headers: customHeaders, ...fetchOptions } = options;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(customHeaders as Record<string, string> || {}),
    };

    if (!skipAuth) {
      const token = this.getToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }

    let res = await fetch(`${API_BASE}${endpoint}`, { ...fetchOptions, headers });

    // Try refresh on 401
    if (res.status === 401 && !skipAuth) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.getToken()}`;
        res = await fetch(`${API_BASE}${endpoint}`, { ...fetchOptions, headers });
      } else {
        this.clearTokens();
        if (typeof window !== 'undefined') window.location.href = '/';
        throw new Error('Session expired');
      }
    }

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }

    return res.json();
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const data = await this.fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    });
    this.setTokens(data.access_token, data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  // Traffic
  getCurrentTraffic() { return this.fetch('/api/traffic/current'); }
  getHistoricalTraffic(params?: string) { return this.fetch(`/api/traffic/historical${params ? '?' + params : ''}`); }
  getHeatmap(source = 'simulation') { return this.fetch(`/api/traffic/heatmap?source=${source}`); }
  getIntersections() { return this.fetch('/api/traffic/intersections'); }

  // AI
  optimizeSignal(data: any) { return this.fetch('/api/ai/optimize', { method: 'POST', body: JSON.stringify(data) }); }
  getPredictions(hours = 6) { return this.fetch(`/api/ai/predictions?hours_ahead=${hours}`); }
  getAIHealth() { return this.fetch('/api/ai/health'); }
  getAIActionLog(params?: string) { return this.fetch(`/api/ai/action-log${params ? '?' + params : ''}`); }
  autoOptimizeAll() { return this.fetch('/api/ai/auto-optimize-all', { method: 'POST' }); }
  revertAIAction(logId: number) { return this.fetch(`/api/ai/revert/${logId}`, { method: 'POST' }); }
  getAutoOptimizeStatus() { return this.fetch('/api/ai/auto-status'); }

  // Analytics
  getAnalyticsSummary() { return this.fetch('/api/analytics/summary'); }
  getHourlyAnalytics(source = 'metro') { return this.fetch(`/api/analytics/hourly?source=${source}`); }
  getWeekdayAnalytics(source = 'metro') { return this.fetch(`/api/analytics/weekday?source=${source}`); }
  getMonthlyAnalytics(source = 'metro') { return this.fetch(`/api/analytics/monthly?source=${source}`); }
  getWeatherImpact(source = 'metro') { return this.fetch(`/api/analytics/weather-impact?source=${source}`); }
  getDistribution(source = 'metro') { return this.fetch(`/api/analytics/distribution?source=${source}`); }
  getPeakHours(source = 'metro') { return this.fetch(`/api/analytics/peak-hours?source=${source}`); }
  getScatterData() { return this.fetch('/api/analytics/scatter'); }
  getSignalComparison() { return this.fetch('/api/analytics/signal-comparison'); }

  // Emergency
  getEmergencyVehicles() { return this.fetch('/api/emergency/vehicles'); }
  getEmergencyDashboard() { return this.fetch('/api/emergency/dashboard'); }
  createEmergencyAlert(data: any) { return this.fetch('/api/emergency/alert', { method: 'POST', body: JSON.stringify(data) }); }
  togglePriority(vehicleId: number, activate: boolean) { return this.fetch(`/api/emergency/priority/${vehicleId}?activate=${activate}`, { method: 'PUT' }); }

  // Incidents
  getIncidents(params?: string) { return this.fetch(`/api/incidents/${params ? '?' + params : ''}`); }
  createIncident(data: any) { return this.fetch('/api/incidents/', { method: 'POST', body: JSON.stringify(data) }); }
  updateIncident(id: number, data: any) { return this.fetch(`/api/incidents/${id}`, { method: 'PUT', body: JSON.stringify(data) }); }
  deleteIncident(id: number) { return this.fetch(`/api/incidents/${id}`, { method: 'DELETE' }); }

  // Notifications
  getNotifications(params?: string) { return this.fetch(`/api/notifications/${params ? '?' + params : ''}`); }
  getUnreadCount() { return this.fetch('/api/notifications/unread-count'); }
  markRead(id: number) { return this.fetch(`/api/notifications/${id}/read`, { method: 'PUT' }); }
  markAllRead() { return this.fetch('/api/notifications/read-all', { method: 'PUT' }); }
  deleteNotification(id: number) { return this.fetch(`/api/notifications/${id}`, { method: 'DELETE' }); }

  // User
  getProfile() { return this.fetch('/api/auth/me'); }
  updateProfile(data: { full_name?: string; phone?: string; department?: string; avatar_url?: string }) {
    return this.fetch('/api/auth/profile', { method: 'PUT', body: JSON.stringify(data) });
  }
  changePassword(current_password: string, new_password: string) {
    return this.fetch('/api/auth/change-password', { method: 'PUT', body: JSON.stringify({ current_password, new_password }) });
  }
}

export const api = new ApiClient();
