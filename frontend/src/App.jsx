import React, { useState, useEffect } from 'react';
import { Music, BarChart3, FileText, Users, Menu, X, TrendingUp, Globe, Calendar } from 'lucide-react';

// Brand colors from Prism Analytics
const brandColors = {
  primary: '#1A1A1A',
  accent: '#E50914', 
  secondary: '#333333',
  background: '#FFFFFF'
};

// Mock API hook
const useApi = () => {
  const get = async (endpoint) => {
    // Simulate API call with mock data
    await new Promise(resolve => setTimeout(resolve, 500));
    
    if (endpoint === '/dashboard/overview') {
      return {
        total_streams: 45267891,
        unique_artists: 1247,
        active_platforms: 8,
        weekly_streams: 2847592,
        growth_percentage: 12.5
      };
    }
    
    if (endpoint === '/artists/trending') {
      return [
        { artist_name: 'Taylor Swift', total_streams: 8934567, growth_percentage: 23.4 },
        { artist_name: 'Bad Bunny', total_streams: 7823456, growth_percentage: 18.7 },
        { artist_name: 'Drake', total_streams: 6754321, growth_percentage: 15.2 },
        { artist_name: 'Olivia Rodrigo', total_streams: 5643210, growth_percentage: 28.9 },
        { artist_name: 'The Weeknd', total_streams: 4532109, growth_percentage: 11.3 }
      ];
    }
    
    if (endpoint === '/analytics/platforms') {
      return [
        { platform_name: 'Spotify', total_value: 15234567, market_share: 45.2, unique_tracks: 3421 },
        { platform_name: 'Apple Music', total_value: 12847593, market_share: 38.1, unique_tracks: 2987 },
        { platform_name: 'YouTube Music', total_value: 3456789, market_share: 10.3, unique_tracks: 1876 },
        { platform_name: 'Amazon Music', total_value: 2165432, market_share: 6.4, unique_tracks: 1234 }
      ];
    }
    
    return {};
  };
  
  return { get };
};

// Loading Spinner Component
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
  </div>
);

// Metrics Card Component
const MetricsCard = ({ title, value, change, icon: Icon, color = 'blue' }) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    red: 'text-red-600 bg-red-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change && (
            <p className={`text-sm mt-1 flex items-center ${
              change > 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              <TrendingUp size={16} className="mr-1" />
              {change > 0 ? '+' : ''}{change}%
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  );
};

// Dashboard Overview Component
const DashboardOverview = () => {
  const { get } = useApi();
  const [data, setData] = useState(null);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [overview, trendingData] = await Promise.all([
          get('/dashboard/overview'),
          get('/artists/trending')
        ]);
        setData(overview);
        setTrending(trendingData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <LoadingSpinner />;

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Total Streams"
          value={formatNumber(data?.total_streams || 0)}
          change={data?.growth_percentage}
          icon={Music}
          color="red"
        />
        <MetricsCard
          title="Unique Artists"
          value={data?.unique_artists || 0}
          icon={Users}
          color="blue"
        />
        <MetricsCard
          title="Active Platforms"
          value={data?.active_platforms || 0}
          icon={Globe}
          color="green"
        />
        <MetricsCard
          title="Weekly Streams"
          value={formatNumber(data?.weekly_streams || 0)}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Trending Artists */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Trending Artists</h2>
          <p className="text-gray-600">Top performers this week</p>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {trending.map((artist, index) => (
              <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center text-white font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{artist.artist_name}</h3>
                    <p className="text-sm text-gray-600">{formatNumber(artist.total_streams)} streams</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    +{artist.growth_percentage}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Platform Analysis Component
const PlatformAnalysis = () => {
  const { get } = useApi();
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlatforms = async () => {
      try {
        const data = await get('/analytics/platforms');
        setPlatforms(data);
      } catch (error) {
        console.error('Failed to fetch platform data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlatforms();
  }, []);

  if (loading) return <LoadingSpinner />;

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Platform Analysis</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Platform Performance</h2>
          <p className="text-gray-600">Market share and performance by platform</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Platform
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Streams
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Share
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unique Tracks
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {platforms.map((platform, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{platform.platform_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                    {formatNumber(platform.total_value)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 h-2 bg-gray-200 rounded-full mr-3">
                        <div 
                          className="h-2 bg-red-600 rounded-full" 
                          style={{ width: `${platform.market_share}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-900">{platform.market_share}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                    {platform.unique_tracks.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Report Builder Component
const ReportBuilder = () => {
  const [selectedArtist, setSelectedArtist] = useState('');
  const [reportType, setReportType] = useState('wrapped');
  const [year, setYear] = useState(2024);
  const [generating, setGenerating] = useState(false);

  const mockArtists = [
    { id: 'artist_1', name: 'Taylor Swift' },
    { id: 'artist_2', name: 'Bad Bunny' },
    { id: 'artist_3', name: 'Drake' },
    { id: 'artist_4', name: 'Olivia Rodrigo' }
  ];

  const handleGenerateReport = async () => {
    if (!selectedArtist) {
      alert('Please select an artist');
      return;
    }

    setGenerating(true);
    
    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    alert(`${reportType === 'wrapped' ? 'Wrapped' : 'Monthly'} report generated for ${mockArtists.find(a => a.id === selectedArtist)?.name}!`);
    setGenerating(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Generate Artist Report</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Artist Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Artist
            </label>
            <select
              value={selectedArtist}
              onChange={(e) => setSelectedArtist(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            >
              <option value="">Choose an artist...</option>
              {mockArtists.map(artist => (
                <option key={artist.id} value={artist.id}>
                  {artist.name}
                </option>
              ))}
            </select>
          </div>

          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            >
              <option value="wrapped">Wrapped Report (Annual)</option>
              <option value="monthly">Monthly Summary</option>
            </select>
          </div>

          {/* Year Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Year
            </label>
            <select
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            >
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
              <option value={2022}>2022</option>
            </select>
          </div>
        </div>

        <div className="mt-8">
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className={`w-full md:w-auto px-6 py-3 rounded-lg font-medium transition-colors ${
              generating
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
          >
            {generating ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating Report...
              </div>
            ) : (
              `Generate ${reportType === 'wrapped' ? 'Wrapped' : 'Monthly'} Report`
            )}
          </button>
        </div>
      </div>

      {/* Report Preview Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Report Preview</h3>
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-8 text-center">
          <FileText size={48} className="mx-auto text-red-600 mb-4" />
          <p className="text-gray-600">
            Select an artist and generate a report to see the preview
          </p>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
    { id: 'platforms', name: 'Platform Analysis', icon: Globe },
    { id: 'reports', name: 'Report Builder', icon: FileText },
  ];

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardOverview />;
      case 'platforms':
        return <PlatformAnalysis />;
      case 'reports':
        return <ReportBuilder />;
      default:
        return <DashboardOverview />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 fixed w-full top-0 z-50">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 lg:hidden"
              >
                <Menu size={20} />
              </button>
              <div className="flex items-center ml-4 lg:ml-0">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
                    <Music className="text-white" size={20} />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold" style={{ color: brandColors.primary }}>
                      PRISM
                    </h1>
                    <p className="text-xs text-gray-500 -mt-1">ANALYTICS</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Music Analytics Platform
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <nav className={`fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}>
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 lg:hidden">
            <span className="text-lg font-semibold text-gray-900">Menu</span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              <X size={20} />
            </button>
          </div>
          
          <div className="pt-4 pb-4 overflow-y-auto">
            <nav className="px-3 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setCurrentView(item.id);
                      setSidebarOpen(false);
                    }}
                    className={`w-full group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                      currentView === item.id
                        ? 'bg-red-50 text-red-700 border-r-2 border-red-600'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon
                      className={`mr-3 h-5 w-5 ${
                        currentView === item.id ? 'text-red-500' : 'text-gray-400 group-hover:text-gray-500'
                      }`}
                    />
                    {item.name}
                  </button>
                );
              })}
            </nav>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-6">
            {renderCurrentView()}
          </div>
        </main>
      </div>

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-gray-600 bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default App;