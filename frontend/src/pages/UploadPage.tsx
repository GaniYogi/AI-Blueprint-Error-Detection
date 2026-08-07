import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { blueprintService } from '../services/api';
import { UploadCloud, FileText, AlertCircle, ArrowRight, RefreshCw } from 'lucide-react';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [isDragActive, setIsDragActive] = useState(false);
  
  // Upload state
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUploadName, setCurrentUploadName] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const data = await blueprintService.list();
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch upload history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleUpload = async (file: File) => {
    // Basic file validation
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['png', 'jpg', 'jpeg', 'pdf'].includes(ext)) {
      setError('Invalid file format. Only JPG, PNG, and PDF files are supported.');
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setError('File size too large. Maximum size is 15MB.');
      return;
    }

    setError(null);
    setUploading(true);
    setCurrentUploadName(file.name);

    try {
      const response = await blueprintService.upload(file);
      // Wait a moment and navigate to results, or refetch history
      // Since it runs in the background, we can navigate directly to the results screen
      // which handles polling/refreshing of the analysis status
      navigate(`/results/${response.id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to upload blueprint.');
      setUploading(false);
    }
  };

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-8 text-left max-w-5xl mx-auto">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight">Upload Blueprints</h2>
        <p className="text-primary-500 text-sm mt-1">Submit architectural layouts in PNG, JPG, or PDF format for AI error diagnostics</p>
      </div>

      {/* Drag & Drop Area */}
      <div 
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`glass-panel border-2 border-dashed rounded-2xl p-12 text-center flex flex-col items-center justify-center transition-all cursor-pointer ${
          isDragActive 
            ? 'border-indigo-500 bg-indigo-500/5 shadow-md shadow-indigo-500/5' 
            : 'border-primary-300 dark:border-primary-800 hover:border-indigo-500/60'
        }`}
      >
        <input 
          type="file" 
          id="file-upload" 
          className="hidden" 
          accept=".png,.jpg,.jpeg,.pdf"
          onChange={onFileChange} 
          disabled={uploading}
        />
        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
          <div className="p-4 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-2xl mb-4">
            {uploading ? (
              <RefreshCw className="h-10 w-10 animate-spin" />
            ) : (
              <UploadCloud className="h-10 w-10" />
            )}
          </div>
          
          {uploading ? (
            <div className="space-y-2">
              <p className="text-lg font-bold">Uploading {currentUploadName}...</p>
              <p className="text-sm text-primary-500">FastAPI is saving the file and initiating background YOLO/OCR analysis.</p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-lg font-bold">Drag & drop blueprint file here</p>
              <p className="text-sm text-primary-500">or <span className="text-indigo-500 font-semibold underline">browse local files</span></p>
              <p className="text-xs text-primary-400">Supports PDF, PNG, JPG, or JPEG (Max 15MB)</p>
            </div>
          )}
        </label>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center space-x-3 text-rose-600 dark:text-rose-400 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload History List */}
      <div className="glass-panel p-6 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-sm">
        <h3 className="text-lg font-bold mb-6">File Submission History</h3>
        
        {loadingHistory ? (
          <div className="flex justify-center py-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : history.length > 0 ? (
          <div className="divide-y divide-primary-100 dark:divide-primary-800/60">
            {history.map((bp: any) => {
              const formattedSize = (bp.file_size / (1024 * 1024)).toFixed(2) + ' MB';
              const dateStr = new Date(bp.created_at).toLocaleDateString(undefined, { 
                month: 'short', 
                day: 'numeric', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              });

              return (
                <div key={bp.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start space-x-3 text-left">
                    <div className="p-2 bg-primary-100 dark:bg-primary-800 rounded-lg text-primary-500 mt-0.5">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-primary-900 dark:text-primary-100 text-sm sm:text-base">{bp.original_name}</p>
                      <div className="flex items-center space-x-2 text-xs text-primary-400 mt-1">
                        <span>{formattedSize}</span>
                        <span>•</span>
                        <span>{dateStr}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 self-end sm:self-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                      bp.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' :
                      bp.status === 'processing' ? 'bg-blue-500/10 text-blue-500 animate-pulse' :
                      bp.status === 'pending' ? 'bg-amber-500/10 text-amber-500' :
                      'bg-rose-500/10 text-rose-500'
                    }`}>
                      {bp.status.toUpperCase()}
                    </span>

                    {bp.status === 'completed' ? (
                      <Link 
                        to={`/results/${bp.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors shadow-sm"
                      >
                        <span>View Results</span>
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    ) : bp.status === 'failed' ? (
                      <div className="text-xs text-rose-500 max-w-[200px] truncate" title={bp.error_message}>
                        Error: {bp.error_message || 'Analysis failed'}
                      </div>
                    ) : (
                      <span className="text-xs text-primary-400 animate-pulse">Running analysis...</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="py-8 text-center text-primary-400 text-sm">No files uploaded yet. Drag a file onto the dashed box to submit.</p>
        )}
      </div>
    </div>
  );
};
