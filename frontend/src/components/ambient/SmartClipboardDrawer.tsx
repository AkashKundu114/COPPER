import React, { useEffect, useState } from 'react';
import { clipboardAPI } from '../../services/api';
import { 
  X, 
  Search, 
  Link, 
  Code, 
  AlertTriangle, 
  FileJson, 
  Mail, 
  File, 
  Type,
  Play,
  RotateCcw,
  Trash2,
  Copy,
  Check
} from 'lucide-react';

export type ClipboardEntryType = 'URL' | 'Code' | 'Error' | 'JSON' | 'Email' | 'FilePath' | 'PlainText';

export interface ClipboardEntry {
  id: string;
  content: string;
  type: ClipboardEntryType;
  timestamp: number;
}

export const SmartClipboardDrawer: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const [history, setHistory] = useState<ClipboardEntry[]>([]);
  const [current, setCurrent] = useState<ClipboardEntry | null>(null);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<ClipboardEntryType | 'All'>('All');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadData();
      const interval = setInterval(loadData, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      const hist = await clipboardAPI.getHistory();
      const curr = await clipboardAPI.getCurrent();
      setHistory(hist as any || []);
      setCurrent(curr as any || null);
    } catch (e) {
      console.error('Failed to load clipboard data', e);
    }
  };

  const handleProcess = async (id: string) => {
    try {
      await clipboardAPI.processEntry(id);
      await loadData();
    } catch (e) {
      console.error('Failed to process entry', e);
    }
  };

  const handleClear = async () => {
    try {
      await clipboardAPI.clearHistory();
      setHistory([]);
    } catch (e) {
      console.error('Failed to clear history', e);
    }
  };

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getTypeIcon = (type: ClipboardEntryType) => {
    switch (type) {
      case 'URL': return <Link className="w-4 h-4 text-blue-400" />;
      case 'Code': return <Code className="w-4 h-4 text-green-400" />;
      case 'Error': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'JSON': return <FileJson className="w-4 h-4 text-yellow-400" />;
      case 'Email': return <Mail className="w-4 h-4 text-purple-400" />;
      case 'FilePath': return <File className="w-4 h-4 text-cyan-400" />;
      case 'PlainText': default: return <Type className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTypeColor = (type: ClipboardEntryType) => {
    switch (type) {
      case 'URL': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'Code': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'Error': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'JSON': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'Email': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'FilePath': return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'PlainText': default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getActionLabel = (type: ClipboardEntryType) => {
    switch (type) {
      case 'URL': return 'Open Link';
      case 'Code': return 'Run Analysis';
      case 'Error': return 'Explain Error';
      case 'JSON': return 'Format JSON';
      case 'Email': return 'Draft Reply';
      case 'FilePath': return 'Open File';
      case 'PlainText': default: return 'Summarize';
    }
  };

  const filteredHistory = history.filter(entry => {
    const matchesSearch = entry.content.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filterType === 'All' || entry.type === filterType;
    return matchesSearch && matchesFilter;
  });

  const types: (ClipboardEntryType | 'All')[] = ['All', 'URL', 'Code', 'Error', 'JSON', 'Email', 'FilePath', 'PlainText'];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-cyan-900/50 shadow-2xl shadow-cyan-900/20 flex flex-col font-mono text-sm text-gray-300 z-50 transform transition-transform duration-300 ease-in-out">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-cyan-900/50 bg-gray-900/80 backdrop-blur-sm">
        <h2 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
          <RotateCcw className="w-5 h-5" />
          Smart Clipboard
        </h2>
        <div className="flex items-center gap-2">
          <button 
            onClick={handleClear}
            className="p-1.5 hover:bg-red-500/20 text-gray-400 hover:text-red-400 rounded transition-colors"
            title="Clear History"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button 
            onClick={onClose}
            className="p-1.5 hover:bg-cyan-500/20 text-gray-400 hover:text-cyan-400 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="p-4 flex flex-col gap-3 border-b border-cyan-900/30">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-cyan-500/50" />
          <input
            type="text"
            placeholder="Search clipboard..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-950 border border-cyan-900/50 rounded pl-9 pr-3 py-1.5 focus:outline-none focus:border-cyan-500/50 text-cyan-50 placeholder-cyan-900/50"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-cyan-900 scrollbar-track-transparent">
          {types.map(type => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2.5 py-1 rounded-full text-xs whitespace-nowrap border transition-colors ${
                filterType === type 
                  ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300' 
                  : 'bg-gray-950 border-gray-800 text-gray-500 hover:border-cyan-900 hover:text-gray-300'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Content Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-cyan-900 scrollbar-track-transparent">
        {current && filterType === 'All' && search === '' && (
          <div className="mb-6">
            <h3 className="text-xs uppercase tracking-wider text-cyan-600 mb-2 font-semibold">Current</h3>
            <ClipboardItem 
              entry={current} 
              onProcess={() => handleProcess(current.id)}
              onCopy={() => handleCopy(current.content, current.id)}
              copied={copiedId === current.id}
              getTypeIcon={getTypeIcon}
              getTypeColor={getTypeColor}
              getActionLabel={getActionLabel}
            />
          </div>
        )}

        <div>
          <h3 className="text-xs uppercase tracking-wider text-cyan-600 mb-2 font-semibold">History</h3>
          {filteredHistory.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No matching entries found
            </div>
          ) : (
             <div className="space-y-3">
              {filteredHistory.map(entry => (
                <ClipboardItem 
                  key={entry.id} 
                  entry={entry} 
                  onProcess={() => handleProcess(entry.id)}
                  onCopy={() => handleCopy(entry.content, entry.id)}
                  copied={copiedId === entry.id}
                  getTypeIcon={getTypeIcon}
                  getTypeColor={getTypeColor}
                  getActionLabel={getActionLabel}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface ClipboardItemProps {
  entry: ClipboardEntry;
  onProcess: () => void;
  onCopy: () => void;
  copied: boolean;
  getTypeIcon: (type: ClipboardEntryType) => React.ReactNode;
  getTypeColor: (type: ClipboardEntryType) => string;
  getActionLabel: (type: ClipboardEntryType) => string;
}

const ClipboardItem: React.FC<ClipboardItemProps> = ({ 
  entry, 
  onProcess, 
  onCopy,
  copied, 
  getTypeIcon, 
  getTypeColor, 
  getActionLabel 
}) => {
  return (
    <div className="group bg-gray-950 border border-gray-800 hover:border-cyan-900/50 rounded-lg overflow-hidden transition-all duration-200">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800 bg-gray-900/50">
        <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${getTypeColor(entry.type)}`}>
          {getTypeIcon(entry.type)}
          {entry.type}
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button 
            onClick={onCopy}
            className="p-1 hover:bg-gray-800 text-gray-400 hover:text-cyan-400 rounded transition-colors"
            title="Copy to clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button 
            onClick={onProcess}
            className="p-1 hover:bg-gray-800 text-gray-400 hover:text-cyan-400 rounded transition-colors"
            title="Reprocess"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      <div className="p-3">
        <div className="text-xs text-gray-300 line-clamp-3 mb-3 font-mono break-all whitespace-pre-wrap">
          {entry.content}
        </div>
        <button className="w-full flex items-center justify-center gap-2 py-1.5 bg-cyan-950/30 hover:bg-cyan-900/50 text-cyan-400 text-xs rounded border border-cyan-900/30 hover:border-cyan-500/50 transition-all group/btn">
          <Play className="w-3 h-3 group-hover/btn:text-cyan-300" />
          {getActionLabel(entry.type)}
        </button>
      </div>
    </div>
  );
};
