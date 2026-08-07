import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { analyticsService } from '../services/api';
import { 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  Plus, 
  Clock, 
  ArrowRight,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Cell 
} from 'recharts';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const res = await analyticsService.dashboard();
      setData(res);
    } catch (err) {
      console.error(err);
      setError('Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 text-center text-rose-500 bg-rose-50 dark:bg-rose-950/30 rounded-xl border border-rose-200 max-w-xl mx-auto mt-12">
        <AlertCircle className="h-10 w-10 mx-auto mb-2 text-rose-500" />
        <p className="font-bold">Error Loading Dashboard</p>
        <p className="text-sm mt-1">{error || 'Data is unavailable'}</p>
        <button onClick={fetchDashboardData} className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold">
          Try Again
        </button>
      </div>
    );
  }

  // Formatting chart data
  const severityChartData = [
    { name: 'Low', count: data.severity_breakdown.Low, fill: '#6366f1' },
    { name: 'Medium', count: data.severity_breakdown.Medium, fill: '#f59e0b' },
    { name: 'High', count: data.severity_breakdown.High, fill: '#ea580c' },
    { name: 'Critical', count: data.severity_breakdown.Critical, fill: '#f43f5e' },
  ];

  const hasChartData = severityChartData.some(d => d.count > 0);

  return (
    <div className="space-y-8 text-left">
      {/* Welcome & Action banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Dashboard Overview</h2>
          <p className="text-primary-500 text-sm mt-1">Real-time status of your blueprint diagnostic reports</p>
        </div>
        <Link 
          to="/upload" 
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm transition-all shadow-md shadow-indigo-600/20"
        >
          <Plus className="h-4 w-4" />
          <span>Upload Blueprint</span>
        </Link>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Card 1 */}
        <div className="glass-card p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/20 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">Total Analyzed</span>
            <h3 className="text-3xl font-extrabold font-heading">{data.total_blueprints}</h3>
          </div>
          <div className="p-3 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-xl">
            <FileText className="h-6 w-6" />
          </div>
        </div>

        {/* Card 2 */}
        <div className="glass-card p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/20 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">Errors Detected</span>
            <h3 className="text-3xl font-extrabold font-heading text-rose-500">{data.total_errors}</h3>
          </div>
          <div className="p-3 bg-rose-500/10 text-rose-500 rounded-xl">
            <AlertTriangle className="h-6 w-6" />
          </div>
        </div>

        {/* Card 3 */}
        <div className="glass-card p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/20 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">Code Violations</span>
            <h3 className="text-3xl font-extrabold font-heading text-amber-500">{data.total_violations}</h3>
          </div>
          <div className="p-3 bg-amber-500/10 text-amber-500 rounded-xl">
            <ShieldCheck className="h-6 w-6" />
          </div>
        </div>

        {/* Card 4 */}
        <div className="glass-card p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/20 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">Avg Compliance</span>
            <h3 className="text-3xl font-extrabold font-heading text-emerald-500">{data.average_compliance_score}%</h3>
          </div>
          <div className="p-3 bg-emerald-500/10 text-emerald-500 rounded-xl">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chart 1: Compliance History */}
        <div className="glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm">
          <h3 className="text-lg font-bold mb-6 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-indigo-500" />
            <span>Compliance Quality Trend</span>
          </h3>
          <div className="h-80">
            {data.compliance_history.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.compliance_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.15} />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                      borderColor: 'rgba(255,255,255,0.1)', 
                      borderRadius: '8px', 
                      color: '#fff' 
                    }} 
                  />
                  <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorScore)" name="Compliance %" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-primary-400">
                <Clock className="h-10 w-10 mb-2 opacity-50" />
                <p className="text-sm">No compliance history data available. Analyze blueprints first.</p>
              </div>
            )}
          </div>
        </div>

        {/* Chart 2: Violations by Severity */}
        <div className="glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm">
          <h3 className="text-lg font-bold mb-6 flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-rose-500" />
            <span>Violations by Severity Level</span>
          </h3>
          <div className="h-80">
            {hasChartData ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.15} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                      borderColor: 'rgba(255,255,255,0.1)', 
                      borderRadius: '8px', 
                      color: '#fff' 
                    }} 
                  />
                  <Bar dataKey="count" name="Violations count" radius={[6, 6, 0, 0]}>
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-primary-400">
                <CheckCircle className="h-10 w-10 mb-2 text-emerald-500/50" />
                <p className="text-sm">No active violations detected in your projects.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Blueprints List */}
      <div className="glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold">Recent Blueprints</h3>
          <Link to="/reports" className="text-xs font-semibold text-indigo-500 hover:text-indigo-400 flex items-center space-x-1">
            <span>View All Reports</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-primary-200 dark:border-primary-800 text-xs font-bold text-primary-500 uppercase tracking-wider">
                <th className="pb-3">Blueprint Name</th>
                <th className="pb-3">Uploaded On</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Compliance Score</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-primary-100 dark:divide-primary-800/60 text-sm">
              {data.recent_blueprints.length > 0 ? (
                data.recent_blueprints.map((bp: any) => {
                  const hasResult = bp.status === 'completed';
                  const dateStr = new Date(bp.created_at).toLocaleDateString(undefined, { 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric' 
                  });
                  
                  return (
                    <tr key={bp.id} className="hover:bg-primary-500/5 transition-colors">
                      <td className="py-4 font-semibold text-primary-900 dark:text-primary-100">{bp.original_name}</td>
                      <td className="py-4 text-primary-500">{dateStr}</td>
                      <td className="py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          bp.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' :
                          bp.status === 'processing' ? 'bg-blue-500/10 text-blue-500 animate-pulse' :
                          bp.status === 'pending' ? 'bg-amber-500/10 text-amber-500' :
                          'bg-rose-500/10 text-rose-500'
                        }`}>
                          {bp.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-4">
                        {hasResult ? (
                          <span className="font-bold font-mono">{bp.analysis_results?.compliance_score}%</span>
                        ) : (
                          <span className="text-primary-400">-</span>
                        )}
                      </td>
                      <td className="py-4 text-right">
                        {hasResult ? (
                          <Link 
                            to={`/results/${bp.id}`} 
                            className="inline-flex items-center space-x-1 px-3 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 text-xs font-bold rounded-lg transition-colors"
                          >
                            <span>Inspect results</span>
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        ) : (
                          <span className="text-xs text-primary-400">Processing...</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-primary-400">
                    No blueprints uploaded yet. Get started by uploading your first design layout.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
