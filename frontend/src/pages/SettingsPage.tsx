import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { rulesService } from '../services/api';
import { Settings, User, Save, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  
  // Rules states
  const [rules, setRules] = useState<any[]>([]);
  const [loadingRules, setLoadingRules] = useState(true);
  const [savingRuleKey, setSavingRuleKey] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchRules = async () => {
    try {
      const data = await rulesService.list();
      setRules(data);
    } catch (err) {
      console.error('Failed to load rules:', err);
      setErrorMsg('Failed to load compliance rules.');
    } finally {
      setLoadingRules(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleRuleValueChange = (key: string, value: number) => {
    setRules(prevRules => 
      prevRules.map(r => r.rule_key === key ? { ...r, current_value: value } : r)
    );
  };

  const handleSaveRule = async (key: string, value: number) => {
    setSavingRuleKey(key);
    setSuccessMsg(null);
    setErrorMsg(null);
    
    try {
      await rulesService.update(key, value);
      setSuccessMsg('Rule threshold updated successfully! Subsequent blueprint audits will use these values.');
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      console.error('Failed to save rule:', err);
      setErrorMsg('Failed to save rule settings.');
    } finally {
      setSavingRuleKey(null);
    }
  };

  return (
    <div className="space-y-8 text-left max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">System Settings</h2>
        <p className="text-primary-500 text-sm mt-1">Configure automated building code parameters and manage developer profile credentials</p>
      </div>

      {/* Messages */}
      {successMsg && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-xl flex items-center space-x-3 text-emerald-600 dark:text-emerald-400 text-sm">
          <CheckCircle className="h-5 w-5 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center space-x-3 text-rose-600 dark:text-rose-400 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Left Column: Building Codes rule engine (8 cols) */}
        <div className="md:col-span-8 glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm space-y-6">
          <div className="flex items-center space-x-2 border-b border-primary-200 dark:border-primary-800 pb-4">
            <Settings className="h-5 w-5 text-indigo-500" />
            <h3 className="text-lg font-bold">Building Code Rule Parameters</h3>
          </div>

          {loadingRules ? (
            <div className="flex justify-center py-10">
              <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
            </div>
          ) : (
            <div className="space-y-6">
              {rules.map((rule) => {
                const isBinary = rule.unit === 'binary';
                return (
                  <div key={rule.rule_key} className="space-y-3 p-4 bg-white/40 dark:bg-primary-900/20 rounded-xl border border-primary-200/40 dark:border-primary-800/40">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-sm text-primary-900 dark:text-primary-100">{rule.name}</h4>
                        <p className="text-xs text-primary-400 mt-0.5">{rule.description}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        rule.severity === 'High' ? 'bg-rose-500/10 text-rose-500' : 'bg-amber-500/10 text-amber-500'
                      }`}>
                        {rule.severity} Severity
                      </span>
                    </div>

                    <div className="flex items-center space-x-4">
                      {isBinary ? (
                        <div className="flex-1 flex items-center space-x-3">
                          <button
                            onClick={() => handleRuleValueChange(rule.rule_key, rule.current_value === 1 ? 0 : 1)}
                            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                              rule.current_value === 1 ? 'bg-indigo-600' : 'bg-primary-300 dark:bg-primary-800'
                            }`}
                          >
                            <span
                              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                                rule.current_value === 1 ? 'translate-x-5' : 'translate-x-0'
                              }`}
                            />
                          </button>
                          <span className="text-xs text-primary-500">
                            {rule.current_value === 1 ? 'Enforce Rule Check' : 'Skip Rule Check'}
                          </span>
                        </div>
                      ) : (
                        <div className="flex-1 space-y-1">
                          <div className="flex justify-between text-xs font-semibold text-primary-500">
                            <span>Threshold value:</span>
                            <span className="font-bold text-primary-900 dark:text-primary-100 font-mono">
                              {rule.current_value} {rule.unit}
                            </span>
                          </div>
                          <input 
                            type="range"
                            min={rule.rule_key === 'min_bedroom_area' ? 50 : (rule.rule_key === 'window_ventilation_ratio' ? 5 : 2)}
                            max={rule.rule_key === 'min_bedroom_area' ? 120 : (rule.rule_key === 'window_ventilation_ratio' ? 15 : 5)}
                            step={rule.rule_key === 'min_bedroom_area' ? 5 : 0.1}
                            value={rule.current_value}
                            onChange={(e) => handleRuleValueChange(rule.rule_key, parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-primary-200 dark:bg-primary-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                          />
                        </div>
                      )}

                      <button
                        onClick={() => handleSaveRule(rule.rule_key, rule.current_value)}
                        disabled={savingRuleKey === rule.rule_key}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors self-end shrink-0 disabled:opacity-50"
                      >
                        {savingRuleKey === rule.rule_key ? (
                          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Save className="h-3.5 w-3.5" />
                        )}
                        <span>Save</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Profile details (4 cols) */}
        <div className="md:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 border-b border-primary-200 dark:border-primary-800 pb-4">
              <User className="h-5 w-5 text-indigo-500" />
              <h3 className="text-lg font-bold">User Profile</h3>
            </div>
            
            {user ? (
              <div className="space-y-4 text-sm">
                <div>
                  <span className="text-xs text-primary-400 block">Full Name</span>
                  <span className="font-semibold text-primary-900 dark:text-primary-100">{user.full_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-primary-400 block">Email Address</span>
                  <span className="font-semibold text-primary-900 dark:text-primary-100">{user.email}</span>
                </div>
                <div>
                  <span className="text-xs text-primary-400 block">Registered on</span>
                  <span className="text-primary-500 font-mono">
                    {new Date(user.created_at).toLocaleDateString(undefined, { 
                      month: 'short', 
                      day: 'numeric', 
                      year: 'numeric' 
                    })}
                  </span>
                </div>
                <div className="pt-2 border-t border-primary-200 dark:border-primary-800 text-[10px] text-primary-400 leading-normal">
                  You are authenticated with developer privileges on this local workspace instance.
                </div>
              </div>
            ) : (
              <p className="text-sm text-primary-400">Not logged in.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
