import { useState, useEffect, useCallback } from 'react';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

// Custom hook for API calls
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const request = useCallback(async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}${endpoint}`;
      const config = {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      };

      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setLoading(false);
      return data;
    } catch (err) {
      setError(err.message);
      setLoading(false);
      throw err;
    }
  }, []);

  const get = useCallback((endpoint) => request(endpoint), [request]);
  
  const post = useCallback((endpoint, data) => 
    request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    }), [request]);

  const put = useCallback((endpoint, data) => 
    request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    }), [request]);

  const del = useCallback((endpoint) => 
    request(endpoint, { method: 'DELETE' }), [request]);

  return { get, post, put, del, loading, error };
};

// Custom hook for dashboard data
export const useDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [trendingArtists, setTrendingArtists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get } = useApi();

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [overview, trending] = await Promise.all([
        get('/dashboard/overview'),
        get('/artists/trending?limit=10')
      ]);

      setDashboardData(overview.data);
      setTrendingArtists(trending.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [get]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return {
    dashboardData,
    trendingArtists,
    loading,
    error,
    refetch: fetchDashboardData
  };
};

// Custom hook for platform analytics
export const usePlatformAnalytics = () => {
  const [platformData, setPlatformData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get } = useApi();

  const fetchPlatformData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await get('/analytics/platforms');
      setPlatformData(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [get]);

  useEffect(() => {
    fetchPlatformData();
  }, [fetchPlatformData]);

  return {
    platformData,
    loading,
    error,
    refetch: fetchPlatformData
  };
};

// Custom hook for artist data
export const useArtist = (artistId) => {
  const [artist, setArtist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get } = useApi();

  const fetchArtist = useCallback(async () => {
    if (!artistId) return;

    try {
      setLoading(true);
      const response = await get(`/artists/${artistId}`);
      setArtist(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [artistId, get]);

  useEffect(() => {
    fetchArtist();
  }, [fetchArtist]);

  return {
    artist,
    loading,
    error,
    refetch: fetchArtist
  };
};

// Custom hook for artist search
export const useArtistSearch = () => {
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { get } = useApi();

  const searchArtists = useCallback(async (query, limit = 20) => {
    if (!query.trim()) {
      setArtists([]);
      return;
    }

    try {
      setLoading(true);
      const response = await get(`/search/artists?q=${encodeURIComponent(query)}&limit=${limit}`);
      setArtists(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [get]);

  return {
    artists,
    loading,
    error,
    searchArtists
  };
};

// Custom hook for report generation
export const useReports = () => {
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState(null);
  const { post } = useApi();

  const generateWrappedReport = useCallback(async (artistId, year, email = null) => {
    try {
      setGeneratingReport(true);
      setReportError(null);

      const response = await post('/reports/generate/wrapped', {
        artist_id: artistId,
        year: year,
        email: email
      });

      setGeneratingReport(false);
      return response.data;
    } catch (err) {
      setReportError(err.message);
      setGeneratingReport(false);
      throw err;
    }
  }, [post]);

  const generateMonthlyReport = useCallback(async (artistId, year, month, email = null) => {
    try {
      setGeneratingReport(true);
      setReportError(null);

      const response = await post('/reports/generate/monthly', {
        artist_id: artistId,
        year: year,
        month: month,
        email: email
      });

      setGeneratingReport(false);
      return response.data;
    } catch (err) {
      setReportError(err.message);
      setGeneratingReport(false);
      throw err;
    }
  }, [post]);

  const previewWrappedReport = useCallback(async (artistId, year) => {
    try {
      setReportError(null);
      
      const response = await post('/reports/preview/wrapped', {
        artist_id: artistId,
        year: year
      });

      return response.data;
    } catch (err) {
      setReportError(err.message);
      throw err;
    }
  }, [post]);

  return {
    generateWrappedReport,
    generateMonthlyReport,
    previewWrappedReport,
    generatingReport,
    reportError
  };
};

// Custom hook for time series data
export const useTimeSeries = (period = 'daily', days = 30) => {
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { get } = useApi();

  const fetchTimeSeriesData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await get(`/analytics/timeseries?period=${period}&days=${days}`);
      setTimeSeriesData(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [get, period, days]);

  useEffect(() => {
    fetchTimeSeriesData();
  }, [fetchTimeSeriesData]);

  return {
    timeSeriesData,
    loading,
    error,
    refetch: fetchTimeSeriesData
  };
};

// Utility functions
export const formatNumber = (num) => {
  if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num?.toString() || '0';
};

export const formatPercentage = (num) => {
  return `${(num || 0).toFixed(1)}%`;
};

export const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

// Local storage utilities
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue];
};

// Custom hook for debounced search
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Custom hook for pagination
export const usePagination = (data, itemsPerPage = 10) => {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(data.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = data.slice(startIndex, endIndex);

  const goToPage = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const nextPage = () => {
    goToPage(currentPage + 1);
  };

  const prevPage = () => {
    goToPage(currentPage - 1);
  };

  return {
    currentData,
    currentPage,
    totalPages,
    goToPage,
    nextPage,
    prevPage,
    hasNext: currentPage < totalPages,
    hasPrev: currentPage > 1
  };
};

// Brand colors constant
export const BRAND_COLORS = {
  primary: '#1A1A1A',
  accent: '#E50914',
  secondary: '#333333',
  background: '#FFFFFF'
};

// Chart color palette
export const CHART_COLORS = [
  '#E50914', // Prism Red
  '#1A1A1A', // Prism Black
  '#333333', // Charcoal Gray
  '#FF6B6B', // Light Red
  '#4ECDC4', // Teal
  '#45B7D1', // Blue
  '#96CEB4', // Green
  '#FFEAA7', // Yellow
  '#DDA0DD', // Plum
  '#98D8C8'  // Mint
];

// Export all hooks and utilities
export default {
  useApi,
  useDashboard,
  usePlatformAnalytics,
  useArtist,
  useArtistSearch,
  useReports,
  useTimeSeries,
  useLocalStorage,
  useDebounce,
  usePagination,
  formatNumber,
  formatPercentage,
  formatDate,
  BRAND_COLORS,
  CHART_COLORS
};