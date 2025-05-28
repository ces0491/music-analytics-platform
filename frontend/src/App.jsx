import React, { useState } from 'react';
import { Music, BarChart3, FileText, Users, Menu, X, TrendingUp, Globe, Calendar } from 'lucide-react';
import { 
  useDashboard, 
  usePlatformAnalytics, 
  useReports, 
  useArtistSearch,
  formatNumber 
} from './hooks/useApi';

// Brand colors from Prism Analytics
const brandColors = {
  primary: '#1A1A1A',
  accent: '#E50914', 
  secondary: '#333333',
  background: '#FFFFFF'
};

// Loading Spinner Component
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
  </div>
);

// Error Component
const ErrorMessage = ({ message, onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
    <div className="text-red-600 mb-4">
      <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    </div>
    <p className="text-red-800 font-medium mb-2">Error Loading Data</p>
    <p className="text-red-600 text-sm mb-4">{message}</p>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
      >
        Try Again
      </button>
    )}
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
          {change !== undefined && (
            <p className={`text-sm mt-1 flex items-center ${
              change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
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
  const { dashboardData, trendingArtists, loading, error, refetch } = useDashboard();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={refetch} />;

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
          value={formatNumber(dashboardData?.total_streams || 0)}
          change={dashboardData?.growth_percentage}
          icon={Music}
          color="red"
        />
        <MetricsCard
          title="Unique Artists"
          value={dashboardData?.unique_artists || 0}
          icon={Users}
          color="blue"
        />
        <MetricsCard
          title="Active Platforms"
          value={dashboardData?.active_platforms || 0}
          icon={Globe}
          color="green"
        />
        <MetricsCard
          title="Weekly Streams"
          value={formatNumber(dashboardData?.weekly_streams || 0)}
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
          {trendingArtists && trendingArtists.length > 0 ? (
            <div className="space-y-4">
              {trendingArtists.map((artist, index) => (
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
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Music size={48} className="mx-auto mb-4 text-gray-300" />
              <p>No trending artists data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Platform Analysis Component
const PlatformAnalysis = () => {
  const { platformData, loading, error, refetch } = usePlatformAnalytics();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={refetch} />;

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
          {platformData && platformData.length > 0 ? (
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
                {platformData.map((platform, index) => (
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
                            style={{ width: `${Math.min(platform.market_share, 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-900">{platform.market_share}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                      {platform.unique_tracks?.toLocaleString() || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <BarChart3 size={48} className="mx-auto mb-4 text-gray-300" />
              <p>No platform data available</p>
            </div>
          )}
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
  const [email, setEmail] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  const { artists, searchArtists } = useArtistSearch();
  const { generateWrappedReport, generateMonthlyReport, generatingReport, reportError } = useReports();

  const handleSearch = (query) => {
    setSearchQuery(query);
    if (query.length > 2) {
      searchArtists(query);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedArtist) {
      alert('Please select an artist');
      return;
    }

    try {
      let result;
      if (reportType === 'wrapped') {
        result = await generateWrappedReport(selectedArtist, year, email || null);
      } else {
        result = await generateMonthlyReport(selectedArtist, year, new Date().getMonth() + 1, email || null);
      }
      
      alert(`Report generated successfully! ${email ? 'Check your email for delivery.' : 'Download link will be available soon.'}`);
    } catch (error) {
      alert(`Failed to generate report: ${error.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Generate Artist Report</h2>
        
        {reportError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{reportError}</p>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Artist Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Artist
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Type artist name..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />
            {artists && artists.length > 0 && (
              <div className="mt-2 max-h-40 overflow-y-auto border border-gray-200 rounded-lg">
                {artists.map((artist) => (
                  <button
                    key={artist.artist_id}
                    onClick={() => {
                      setSelectedArtist(artist.artist_id);
                      setSearchQuery(artist.artist_name);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 focus:bg-gray-50"
                  >
                    <div className="font-medium">{artist.artist_name}</div>
                    <div className="text-sm text-gray-500">
                      {formatNumber(artist.total_streams || 0)} streams
                    </div>
                  </button>
                ))}
              </div>
            )}
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

          {/* Email (Optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email (Optional)
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Send report via email"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />
          </div>
        </div>

        <div className="mt-8">
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport || !selectedArtist}
            className={`w-full md:w-auto px-6 py-3 rounded-lg font-medium transition-colors ${
              generatingReport || !selectedArtist
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
          >
            {generatingReport ? (
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
            {selectedArtist 
              ? `Ready to generate ${reportType} report for ${searchQuery}`
              : 'Select an artist and generate a report to see the preview'
            }
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