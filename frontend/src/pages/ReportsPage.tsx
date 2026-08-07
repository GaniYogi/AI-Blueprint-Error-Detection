import React, { useState, useEffect } from 'react';
import { blueprintService } from '../services/api';
import { FileText, Download, ShieldCheck, Clock, AlertTriangle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ReportsPage: React.FC = () => {
  const [blueprints, setBlueprints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    try {
      const data = await blueprintService.list();
      setBlueprints(data);
    } catch (err) {
      console.error('Failed to load reports list:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // Filter completed blueprints with reports
  const completedBlueprints = blueprints.filter(bp => bp.status === 'completed');

  return (
    <div className="space-y-8 text-left max-w-5xl mx-auto">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Compliance Reports</h2>
        <p className="text-primary-500 text-sm mt-1">Download official PDF audit reports detailing drawing errors and building code validations</p>
      </div>

      {/* Overview stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/20 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">Reports Ready</span>
            <h3 className="text-3xl font-extrabold font-heading text-indigo-600 dark:text-indigo-400">{completedBlueprints.length}</h3>
          </div>
          <div className="p-3 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-xl">
            <FileText className="h-6 w-6" />
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/20 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">Pending Analysis</span>
            <h3 className="text-3xl font-extrabold font-heading text-amber-500">
              {blueprints.filter(bp => ['pending', 'processing'].includes(bp.status)).length}
            </h3>
          </div>
          <div className="p-3 bg-amber-500/10 text-amber-500 rounded-xl">
            <Clock className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Reports List Table */}
      <div className="glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm">
        <h3 className="text-lg font-bold mb-6">Generated Reports</h3>

        {completedBlueprints.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-primary-200 dark:border-primary-800 text-xs font-bold text-primary-500 uppercase tracking-wider">
                  <th className="pb-3">Blueprint drawing</th>
                  <th className="pb-3">Code violations</th>
                  <th className="pb-3">Compliance Score</th>
                  <th className="pb-3">Audit Date</th>
                  <th className="pb-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-primary-100 dark:divide-primary-800/60 text-sm">
                {completedBlueprints.map((bp) => {
                  const dateStr = new Date(bp.created_at).toLocaleDateString(undefined, { 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric' 
                  });
                  const ar = bp.analysis_results;

                  return (
                    <tr key={bp.id} className="hover:bg-primary-500/5 transition-colors">
                      <td className="py-4 font-semibold text-primary-900 dark:text-primary-100 flex items-center space-x-2">
                        <FileText className="h-4.5 w-4.5 text-indigo-500 shrink-0" />
                        <span className="truncate max-w-[240px]" title={bp.original_name}>{bp.original_name}</span>
                      </td>
                      <td className="py-4">
                        {ar?.total_violations > 0 ? (
                          <span className="text-rose-500 font-semibold flex items-center space-x-1">
                            <AlertTriangle className="h-4 w-4 shrink-0" />
                            <span>{ar.total_violations} Failures</span>
                          </span>
                        ) : (
                          <span className="text-emerald-500 font-semibold flex items-center space-x-1">
                            <ShieldCheck className="h-4 w-4 shrink-0" />
                            <span>Compliant</span>
                          </span>
                        )}
                      </td>
                      <td className="py-4 font-mono font-bold">{ar?.compliance_score || 0}%</td>
                      <td className="py-4 text-primary-500">{dateStr}</td>
                      <td className="py-4 text-right flex items-center justify-end space-x-2">
                        <Link 
                          to={`/results/${bp.id}`}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 bg-primary-100 dark:bg-primary-800 hover:bg-primary-200 dark:hover:bg-primary-700 text-primary-700 dark:text-primary-300 text-xs font-bold rounded-lg transition-colors"
                        >
                          <span>Inspect plan</span>
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                        <a 
                          href={blueprintService.getReportUrl(bp.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors shadow-sm"
                        >
                          <Download className="h-3.5 w-3.5" />
                          <span>PDF Report</span>
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="py-8 text-center text-primary-400 text-sm">
            No completed blueprint reports found. Go to the <Link to="/upload" className="text-indigo-500 underline font-semibold">Upload page</Link> to scan architectural layouts.
          </p>
        )}
      </div>
    </div>
  );
};
