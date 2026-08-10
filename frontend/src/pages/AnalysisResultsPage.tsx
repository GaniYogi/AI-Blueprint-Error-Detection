import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { blueprintService } from '../services/api';
import {
  ShieldCheck,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  RefreshCw,
  Eye,
  EyeOff,
  HelpCircle,
  CheckCircle2,
  XCircle,
  AlertCircle
} from 'lucide-react';

export const AnalysisResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const blueprintId = parseInt(id || '0');

  const [blueprint, setBlueprint] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'compliance' | 'errors' | 'objects' | 'ocr'>('compliance');

  // Viewer toggles
  const [showObjects, setShowObjects] = useState(true);
  const [showErrors, setShowErrors] = useState(true);
  const [showOCR, setShowOCR] = useState(false);
  const [hoveredItemId, setHoveredItemId] = useState<string | null>(null);

  // Zoom & Pan states
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });

  const fetchBlueprint = async (isPoll = false) => {
    try {
      const data = await blueprintService.get(blueprintId);
      setBlueprint(data);
      if (data.status === 'pending' || data.status === 'processing') {
        // Continue polling
        setTimeout(() => fetchBlueprint(true), 3000);
      } else {
        // Stop loading even when the completed result came from polling.
        setLoading(false);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch analysis details.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlueprint();
  }, [blueprintId]);

  const handleReanalyze = async () => {
    setLoading(true);
    try {
      await blueprintService.analyze(blueprintId);
      fetchBlueprint();
    } catch (err) {
      console.error(err);
      setError('Failed to trigger re-analysis.');
      setLoading(false);
    }
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.6));
  const handleResetZoom = () => {
    setZoom(1);
    setPanX(0);
    setPanY(0);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left click
    setIsPanning(true);
    panStart.current = { x: e.clientX - panX, y: e.clientY - panY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setPanX(e.clientX - panStart.current.x);
    setPanY(e.clientY - panStart.current.y);
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  if (loading && (!blueprint || blueprint.status === 'pending' || blueprint.status === 'processing')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="h-10 w-10 text-indigo-600 animate-spin" />
        <div className="text-center">
          <p className="font-bold text-lg">AI Blueprint Engine is running...</p>
          <p className="text-sm text-primary-500 max-w-sm mt-1">
            Running computer vision models for wall/door detection, EasyOCR text extraction, and rule evaluation.
          </p>
        </div>
      </div>
    );
  }

  if (error || !blueprint) {
    return (
      <div className="p-6 text-center text-rose-500 bg-rose-50 dark:bg-rose-950/30 rounded-xl border border-rose-200 max-w-xl mx-auto mt-12">
        <AlertCircle className="h-10 w-10 mx-auto mb-2 text-rose-500" />
        <p className="font-bold">Error Loading Analysis</p>
        <p className="text-sm mt-1">{error || 'Data is unavailable'}</p>
        <Link to="/upload" className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold">
          Back to Upload
        </Link>
      </div>
    );
  }

  if (blueprint.status === 'failed') {
    return (
      <div className="p-8 text-center bg-rose-50 dark:bg-rose-950/30 rounded-xl border border-rose-200 max-w-xl mx-auto mt-12 space-y-4">
        <XCircle className="h-12 w-12 mx-auto text-rose-500" />
        <div>
          <h3 className="font-bold text-lg text-rose-600">Analysis Engine Failed</h3>
          <p className="text-sm text-primary-500 mt-2">
            The computer vision parser encountered an error while processing the uploaded drawing.
          </p>
          <div className="p-3 bg-primary-900/10 dark:bg-primary-950/60 rounded text-xs font-mono text-left text-primary-600 dark:text-primary-300 mt-4 overflow-x-auto">
            {blueprint.error_message || 'Unknown processing error'}
          </div>
        </div>
        <div className="flex justify-center space-x-3 pt-2">
          <Link to="/upload" className="px-4 py-2 bg-primary-100 dark:bg-primary-800 text-primary-700 dark:text-primary-300 rounded-lg text-sm font-semibold">
            Back to Upload
          </Link>
          <button onClick={handleReanalyze} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold flex items-center space-x-1">
            <RefreshCw className="h-4 w-4" />
            <span>Retry Analysis</span>
          </button>
        </div>
      </div>
    );
  }

  // Parse results from analysis
  const results = blueprint.analysis_results ? JSON.parse(blueprint.analysis_results.raw_json) : null;
  if (!results) {
    return <div className="text-center py-12">No analysis outputs available. Try re-running.</div>;
  }

  const {
    image_metadata = { width: 1, height: 1 },
    detected_objects = [],
    ocr_results = [],
    errors: engineErrors = [],
    compliance_checks = [],
    compliance_score = 0,
    total_violations = 0,
    risk_assessment = 'Review',
  } = results;

  const imgW = Number(image_metadata?.width) || 1;
  const imgH = Number(image_metadata?.height) || 1;

  // Convert backend [x, y, width, height] boxes to CSS percentages.
  // Some errors can have bbox: null, so handle invalid boxes safely.
  const getBBoxPercentage = (bbox: any): React.CSSProperties | null => {
    if (!Array.isArray(bbox) || bbox.length < 4) {
      return null;
    }

    const [x, y, w, h] = bbox.map(Number);

    if (![x, y, w, h].every(Number.isFinite)) {
      return null;
    }

    return {
      left: `${(x / imgW) * 100}%`,
      top: `${(y / imgH) * 100}%`,
      width: `${(w / imgW) * 100}%`,
      height: `${(h / imgH) * 100}%`,
    };
  };

  const imageUrl = blueprintService.getImageUrl(blueprint.id);

  return (
    <div className="space-y-6 text-left">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-primary-500 text-xs font-semibold">
            <Link to="/dashboard" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <span>Blueprints</span>
            <span>/</span>
            <span className="text-primary-600 dark:text-primary-300">{blueprint.original_name}</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-1">{blueprint.original_name}</h2>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReanalyze}
            className="inline-flex items-center space-x-1.5 px-4 py-2 border border-primary-200 dark:border-primary-800 hover:bg-primary-100 dark:hover:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded-xl text-sm font-semibold transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Re-run Audit</span>
          </button>
          <a
            href={blueprintService.getReportUrl(blueprint.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition-all shadow-md shadow-indigo-600/20"
          >
            <Download className="h-4 w-4" />
            <span>Download Report</span>
          </a>
        </div>
      </div>

      {/* Main Double-Pane Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

        {/* Left Pane: Visualizer Canvas (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="glass-panel rounded-2xl border border-primary-200/50 dark:border-primary-800/30 overflow-hidden shadow-md flex flex-col">
            {/* Visualizer Header Controls */}
            <div className="px-4 py-3 bg-primary-100/50 dark:bg-primary-900/40 border-b border-primary-200 dark:border-primary-800/60 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                {/* Overlay toggles */}
                <button
                  onClick={() => setShowObjects(!showObjects)}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${showObjects ? 'bg-indigo-600 text-white' : 'bg-primary-200 dark:bg-primary-800 text-primary-600 dark:text-primary-400'
                    }`}
                >
                  {showObjects ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
                  <span>Detected Elements</span>
                </button>

                <button
                  onClick={() => setShowErrors(!showErrors)}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${showErrors ? 'bg-rose-600 text-white' : 'bg-primary-200 dark:bg-primary-800 text-primary-600 dark:text-primary-400'
                    }`}
                >
                  {showErrors ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
                  <span>Errors</span>
                </button>

                <button
                  onClick={() => setShowOCR(!showOCR)}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${showOCR ? 'bg-emerald-600 text-white' : 'bg-primary-200 dark:bg-primary-800 text-primary-600 dark:text-primary-400'
                    }`}
                >
                  {showOCR ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
                  <span>Extracted OCR</span>
                </button>
              </div>

              {/* Zoom controls */}
              <div className="flex items-center space-x-1 bg-white dark:bg-primary-900 border border-primary-200 dark:border-primary-800/80 rounded-lg p-1">
                <button onClick={handleZoomOut} className="p-1 hover:bg-primary-100 dark:hover:bg-primary-800 text-primary-500 rounded" title="Zoom Out">
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-xs font-mono px-2 font-bold text-primary-600 dark:text-primary-400">{Math.round(zoom * 100)}%</span>
                <button onClick={handleZoomIn} className="p-1 hover:bg-primary-100 dark:hover:bg-primary-800 text-primary-500 rounded" title="Zoom In">
                  <ZoomIn className="h-4 w-4" />
                </button>
                <div className="w-[1px] h-4 bg-primary-200 dark:bg-primary-800 mx-1"></div>
                <button onClick={handleResetZoom} className="p-1 hover:bg-primary-100 dark:hover:bg-primary-800 text-primary-500 rounded" title="Reset View">
                  <Maximize2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Canvas Interactive viewport */}
            <div
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className={`relative flex-1 bg-slate-900 overflow-hidden aspect-[4/3] select-none ${isPanning ? 'cursor-grabbing' : 'cursor-grab'
                }`}
            >
              {/* Scale & translation wrapper */}
              <div
                style={{
                  transform: `scale(${zoom}) translate(${panX / zoom}px, ${panY / zoom}px)`,
                  transformOrigin: 'center center',
                  transition: isPanning ? 'none' : 'transform 0.1s ease-out',
                }}
                className="relative w-full h-full flex items-center justify-center pointer-events-none"
              >
                {/* Blueprint Image */}
                <div className="relative max-w-full max-h-full pointer-events-auto">
                  <img
                    src={imageUrl}
                    alt="Blueprint Analysis View"
                    className="max-w-full max-h-full block object-contain"
                  />

                  {/* Overlays SVG overlay/absolute HTML cards */}

                  {/* 1. Object Detections */}
                  {showObjects && detected_objects.map((obj: any) => {
                    const rectStyle = getBBoxPercentage(obj.bbox);
                    const isHovered = hoveredItemId === obj.id;
                    const isRoom = obj.label === 'room';

                    if (!rectStyle) {
                      return null;
                    }

                    if (isRoom) {
                      return (
                        <div
                          key={obj.id}
                          style={rectStyle}
                          className={`absolute border-[1.5px] rounded border-dashed transition-colors flex items-center justify-center p-2 text-center ${isHovered
                              ? 'border-indigo-400 bg-indigo-500/25 z-20'
                              : 'border-indigo-500/50 bg-indigo-500/5 hover:border-indigo-400 z-10'
                            }`}
                          onMouseEnter={() => setHoveredItemId(obj.id)}
                          onMouseLeave={() => setHoveredItemId(null)}
                        >
                          <span className="text-[10px] sm:text-xs font-bold text-white px-1.5 py-0.5 bg-indigo-950/80 rounded border border-indigo-500 shadow-sm leading-none">
                            {obj.name || obj.label.toUpperCase()}
                          </span>
                        </div>
                      );
                    }

                    // For doors, windows, columns
                    const colorClasses =
                      obj.label === 'door' ? 'border-sky-500 bg-sky-500/10' :
                        obj.label === 'window' ? 'border-teal-500 bg-teal-500/10' :
                          'border-indigo-300 bg-indigo-300/10';

                    return (
                      <div
                        key={obj.id}
                        style={rectStyle}
                        className={`absolute border transition-colors ${colorClasses} ${isHovered ? 'ring-2 ring-white scale-102 z-20' : 'z-10'}`}
                        onMouseEnter={() => setHoveredItemId(obj.id)}
                        onMouseLeave={() => setHoveredItemId(null)}
                        title={`${obj.label.toUpperCase()} (${Math.round(obj.confidence * 100)}%)`}
                      />
                    );
                  })}

                  {/* 2. Errors & Warnings */}
                  {showErrors && engineErrors.map((err: any) => {
                    const rectStyle = getBBoxPercentage(err.bbox);
                    const isHovered = hoveredItemId === err.id;

                    if (!rectStyle) {
                      return null;
                    }
                    const colorClass =
                      err.severity === 'Critical' ? 'border-rose-600 bg-rose-600/20' :
                        err.severity === 'High' ? 'border-rose-500 bg-rose-500/15' :
                          err.severity === 'Medium' ? 'border-amber-500 bg-amber-500/15' :
                            'border-blue-500 bg-blue-500/15';

                    const pulseClass = (err.severity === 'Critical' || err.severity === 'High') ? 'animate-pulse' : '';

                    return (
                      <div
                        key={err.id}
                        style={rectStyle}
                        className={`absolute border-2 rounded ${colorClass} ${pulseClass} transition-all ${isHovered ? 'ring-2 ring-white scale-105 z-30' : 'z-20'
                          }`}
                        onMouseEnter={() => setHoveredItemId(err.id)}
                        onMouseLeave={() => setHoveredItemId(null)}
                      >
                        <div className={`absolute -top-6 left-0 px-2 py-0.5 rounded text-[8px] sm:text-[10px] font-bold text-white shadow-md leading-none ${err.severity === 'Critical' || err.severity === 'High' ? 'bg-rose-600' : 'bg-amber-500'
                          }`}>
                          {err.type.replace('_', ' ').toUpperCase()}
                        </div>
                      </div>
                    );
                  })}

                  {/* 3. OCR Text */}
                  {showOCR && ocr_results.map((ocr: any) => {
                    const rectStyle = getBBoxPercentage(ocr.bbox);

                    if (!rectStyle) {
                      return null;
                    }

                    return (
                      <div
                        key={ocr.id}
                        style={rectStyle}
                        className="absolute border border-emerald-500/40 bg-emerald-950/70 flex items-center justify-center overflow-hidden z-10"
                        title={`OCR: ${ocr.text}`}
                      >
                        <span className="text-[6px] sm:text-[9px] font-mono text-emerald-400 font-bold leading-none select-text whitespace-nowrap">
                          {ocr.text}
                        </span>
                      </div>
                    );
                  })}

                </div>
              </div>
            </div>

            {/* Instruction Footer */}
            <div className="px-4 py-2 bg-slate-900 border-t border-primary-800 text-[11px] text-primary-400 flex items-center space-x-1.5">
              <HelpCircle className="h-3.5 w-3.5 text-primary-500" />
              <span>Left-click and drag image to Pan. Scroll or use controls to Zoom. Hover items on plan or lists to highlight.</span>
            </div>
          </div>
        </div>

        {/* Right Pane: Diagnostic Tabs (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel rounded-2xl border border-primary-200/50 dark:border-primary-800/30 overflow-hidden shadow-md">
            {/* Sidebar Tabs */}
            <div className="flex border-b border-primary-200 dark:border-primary-800/60 text-xs font-bold bg-primary-100/50 dark:bg-primary-900/40">
              <button
                onClick={() => setActiveTab('compliance')}
                className={`flex-1 py-3 text-center border-b-2 transition-colors ${activeTab === 'compliance'
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-bold'
                    : 'border-transparent text-primary-500 hover:text-primary-700'
                  }`}
              >
                Compliance
              </button>
              <button
                onClick={() => setActiveTab('errors')}
                className={`flex-1 py-3 text-center border-b-2 transition-colors ${activeTab === 'errors'
                    ? 'border-rose-600 text-rose-600 dark:text-rose-400 font-bold'
                    : 'border-transparent text-primary-500 hover:text-primary-700'
                  }`}
              >
                Errors ({engineErrors.length})
              </button>
              <button
                onClick={() => setActiveTab('objects')}
                className={`flex-1 py-3 text-center border-b-2 transition-colors ${activeTab === 'objects'
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-bold'
                    : 'border-transparent text-primary-500 hover:text-primary-700'
                  }`}
              >
                Elements
              </button>
              <button
                onClick={() => setActiveTab('ocr')}
                className={`flex-1 py-3 text-center border-b-2 transition-colors ${activeTab === 'ocr'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400 font-bold'
                    : 'border-transparent text-primary-500 hover:text-primary-700'
                  }`}
              >
                OCR
              </button>
            </div>

            {/* Tab Body */}
            <div className="p-5 max-h-[500px] overflow-y-auto no-scrollbar">

              {/* Tab 1: Compliance */}
              {activeTab === 'compliance' && (
                <div className="space-y-6">
                  {/* Gauge indicator */}
                  <div className="flex items-center space-x-4">
                    <div className="relative h-20 w-20 flex items-center justify-center rounded-full bg-slate-900 border-4 border-indigo-600/30">
                      <span className="text-xl font-extrabold font-mono text-indigo-500">{compliance_score}%</span>
                    </div>
                    <div>
                      <h4 className="font-bold text-base">Compliance Score</h4>
                      <p className="text-xs text-primary-500 mt-0.5">Overall rating: <b>{risk_assessment}</b></p>
                      <p className="text-xs text-rose-500 mt-1"><b>{total_violations} code violations</b> flagged</p>
                    </div>
                  </div>

                  {/* Rules Run audit list */}
                  <div className="space-y-3">
                    <h5 className="text-xs font-bold text-primary-500 uppercase tracking-wider">Building Code Audits</h5>
                    {compliance_checks.map((chk: any, index: number) => {
                      const isPass = chk.status === 'PASS';
                      return (
                        <div key={index} className="p-3 rounded-xl border border-primary-200/40 dark:border-primary-800/40 bg-white/40 dark:bg-primary-900/30 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-xs text-primary-900 dark:text-primary-100">{chk.name}</span>
                            <span className={`inline-flex items-center space-x-0.5 text-[9px] font-bold px-1.5 py-0.5 rounded ${isPass ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
                              }`}>
                              {isPass ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                              <span>{chk.status}</span>
                            </span>
                          </div>
                          <p className="text-[10px] text-primary-400">{chk.description}</p>
                          <div className="flex justify-between text-[10px] pt-1 font-mono border-t border-primary-100 dark:border-primary-800/40 mt-1 text-primary-500">
                            <span>Code threshold: {chk.threshold}</span>
                            <span>Detected: {chk.actual}</span>
                          </div>
                          {!isPass && (
                            <p className="text-[10px] text-amber-500 pt-1 leading-snug">
                              <b>Correction:</b> {chk.suggestion}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Tab 2: Errors */}
              {activeTab === 'errors' && (
                <div className="space-y-4">
                  <h5 className="text-xs font-bold text-primary-500 uppercase tracking-wider mb-2">Flagged Drafting Errors</h5>
                  {engineErrors.length > 0 ? (
                    engineErrors.map((err: any) => {
                      const isHovered = hoveredItemId === err.id;
                      const sevColors =
                        err.severity === 'Critical' ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' :
                          err.severity === 'High' ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' :
                            err.severity === 'Medium' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                              'bg-blue-500/10 text-blue-500 border-blue-500/20';

                      return (
                        <div
                          key={err.id}
                          className={`p-3.5 rounded-xl border transition-all text-xs space-y-2 cursor-pointer ${isHovered
                              ? 'border-rose-500 bg-rose-500/10 ring-1 ring-rose-500/30'
                              : 'border-primary-200/40 dark:border-primary-800/40 bg-white/40 dark:bg-primary-900/30'
                            }`}
                          onMouseEnter={() => setHoveredItemId(err.id)}
                          onMouseLeave={() => setHoveredItemId(null)}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-extrabold text-primary-900 dark:text-primary-100 capitalize">{err.type.replace('_', ' ')}</span>
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${sevColors}`}>
                              {err.severity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-primary-500 leading-snug">{err.description}</p>
                          <div className="pt-2 border-t border-primary-200/40 dark:border-primary-800/40 text-primary-600 dark:text-primary-400">
                            <b className="text-primary-700 dark:text-primary-300">Suggestion:</b> {err.suggestion}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-center py-8 text-primary-400">No drawing errors found.</div>
                  )}
                </div>
              )}

              {/* Tab 3: Objects */}
              {activeTab === 'objects' && (
                <div className="space-y-4">
                  <h5 className="text-xs font-bold text-primary-500 uppercase tracking-wider mb-2">Detected Blueprint Elements</h5>

                  {/* Summary grid counts */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {['room', 'wall', 'door', 'window', 'column', 'staircase'].map((lbl) => {
                      const count = detected_objects.filter((obj: any) => obj.label === lbl).length;
                      return (
                        <div key={lbl} className="p-3 bg-primary-100/50 dark:bg-primary-900/40 border border-primary-200/40 dark:border-primary-800/40 rounded-xl">
                          <span className="text-[10px] uppercase font-bold text-primary-500 tracking-wider block">{lbl}s</span>
                          <span className="text-xl font-extrabold font-heading">{count}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* List of rooms */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-primary-500 uppercase tracking-wider block">Habitable Spaces</span>
                    {detected_objects.filter((o: any) => o.label === 'room').map((room: any) => (
                      <div
                        key={room.id}
                        className={`p-2.5 rounded-lg border border-primary-200/40 dark:border-primary-800/40 text-xs flex justify-between items-center cursor-pointer transition-colors ${hoveredItemId === room.id ? 'bg-indigo-500/10 border-indigo-500/30' : 'bg-white/40 dark:bg-primary-900/20'
                          }`}
                        onMouseEnter={() => setHoveredItemId(room.id)}
                        onMouseLeave={() => setHoveredItemId(null)}
                      >
                        <span className="font-semibold">{room.name || 'Room Space'}</span>
                        <span className="font-mono text-primary-400 text-[10px]">Conf: {Math.round(room.confidence * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 4: OCR */}
              {activeTab === 'ocr' && (
                <div className="space-y-4">
                  <h5 className="text-xs font-bold text-primary-500 uppercase tracking-wider mb-2">Extracted Plan Annotations</h5>
                  <div className="divide-y divide-primary-100 dark:divide-primary-800/40">
                    {ocr_results.map((ocr: any) => (
                      <div key={ocr.id} className="py-2 text-xs flex justify-between gap-4">
                        <span className="font-mono text-primary-800 dark:text-emerald-400 font-bold select-text">{ocr.text}</span>
                        <span className="text-primary-400 text-[10px] shrink-0 font-mono">Conf: {Math.round(ocr.confidence * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          </div>

          {/* Action Recommendations Box */}
          <div className="glass-panel p-5 rounded-2xl border border-primary-200/50 dark:border-primary-800/30 shadow-md space-y-4">
            <h4 className="font-bold text-sm flex items-center space-x-1.5">
              <ShieldCheck className="h-4.5 w-4.5 text-indigo-500" />
              <span>Architectural Advisory</span>
            </h4>
            <div className="text-xs text-primary-600 dark:text-primary-400 space-y-2 max-h-[220px] overflow-y-auto no-scrollbar">
              {(results.recommendations || []).map((rec: string, index: number) => (
                <div key={index} className="flex items-start space-x-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0"></span>
                  <p className="leading-relaxed">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
