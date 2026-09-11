import React, { useState, useEffect } from 'react';
import { emailAPI } from '../services/api';

type Priority = 'Urgent' | 'Needs Response' | 'FYI' | 'Spam';

interface Email {
  id: string;
  from: string;
  subject: string;
  date: string;
  body: string;
  priority: Priority;
}

interface Draft {
  id: string;
  emailId: string;
  body: string;
  guardianScreened: boolean;
}

export const EmailView: React.FC = () => {
  const [isConfigured, setIsConfigured] = useState<boolean>(false);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<Priority | 'Drafts'>('Urgent');
  
  const [inbox, setInbox] = useState<Email[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  
  const [configHost, setConfigHost] = useState('');
  const [configUser, setConfigUser] = useState('');
  const [configPass, setConfigPass] = useState('');

  const loadInitialState = async () => {
    try {
      const res = await emailAPI.isConfigured();
      const configured = Boolean(res.data?.configured);
      setIsConfigured(configured);
      if (configured) {
        fetchEmails(activeTab === 'Drafts' ? 'Urgent' : activeTab);
        fetchDrafts();
      } else {
        setShowConfigModal(true);
      }
    } catch (error) {
      console.error('Failed to load email state:', error);
    }
  };

  useEffect(() => {
    loadInitialState();
  }, []);

  useEffect(() => {
    if (isConfigured && activeTab !== 'Drafts') {
      fetchEmails(activeTab as Priority);
    }
  }, [activeTab, isConfigured]);

  const fetchEmails = async (priority: Priority) => {
    try {
      const res = await emailAPI.getInbox(priority);
      setInbox(res.data || []);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    }
  };

  const fetchDrafts = async () => {
    try {
      const res = await emailAPI.getDrafts();
      setDrafts(res.data || []);
    } catch (error) {
      console.error('Failed to fetch drafts:', error);
    }
  };

  const handleSync = async () => {
    try {
      await emailAPI.fetch();
      if (activeTab !== 'Drafts') {
        fetchEmails(activeTab as Priority);
      }
      fetchDrafts();
    } catch (error) {
      console.error('Sync failed:', error);
    }
  };

  const handleConfigure = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await emailAPI.configure({
        host: configHost,
        port: 993,
        username: configUser,
        password: configPass,
        use_ssl: true,
      });
      setIsConfigured(true);
      setShowConfigModal(false);
      handleSync();
    } catch (error) {
      console.error('Configuration failed:', error);
    }
  };

  const generateDraft = async (emailId: string) => {
    try {
      await emailAPI.draftResponse(emailId);
      fetchDrafts();
    } catch (error) {
      console.error('Failed to generate draft:', error);
    }
  };

  const handleApproveDraft = async (id: string) => {
    try {
      await emailAPI.approveDraft(id);
      fetchDrafts();
    } catch (error) {
      console.error('Failed to approve draft:', error);
    }
  };

  const handleRejectDraft = async (id: string) => {
    try {
      await emailAPI.rejectDraft(id);
      fetchDrafts();
    } catch (error) {
      console.error('Failed to reject draft:', error);
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-900/80 border border-slate-800 font-mono text-xs text-cyber-cyan p-4">
      <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
        <h2 className="text-accent-400 text-lg uppercase tracking-wider">Comms Uplink</h2>
        <div className="flex gap-2">
          {!isConfigured ? (
            <button 
              onClick={() => setShowConfigModal(true)}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-accent-400 border border-accent-400/30 rounded"
            >
              Configure IMAP
            </button>
          ) : (
            <button 
              onClick={handleSync}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-cyber-cyan border border-cyber-cyan/30 rounded"
            >
              [ SYNC ]
            </button>
          )}
        </div>
      </div>

      {showConfigModal && (
        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-md shadow-2xl max-w-sm w-full">
            <h3 className="text-accent-400 text-sm mb-4 uppercase">IMAP Configuration</h3>
            <form onSubmit={handleConfigure} className="flex flex-col gap-3">
              <input 
                type="text" placeholder="Host" 
                value={configHost} onChange={e => setConfigHost(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-cyber-cyan p-2 outline-none focus:border-accent-400"
              />
              <input 
                type="text" placeholder="Username" 
                value={configUser} onChange={e => setConfigUser(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-cyber-cyan p-2 outline-none focus:border-accent-400"
              />
              <input 
                type="password" placeholder="Password" 
                value={configPass} onChange={e => setConfigPass(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-cyber-cyan p-2 outline-none focus:border-accent-400"
              />
              <div className="flex justify-end gap-2 mt-4">
                <button type="button" onClick={() => setShowConfigModal(false)} className="px-3 py-1 hover:text-red-400">Cancel</button>
                <button type="submit" className="px-3 py-1 bg-slate-800 text-accent-400 border border-accent-400 hover:bg-slate-700 rounded">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="flex gap-4 h-full overflow-hidden">
        {/* Sidebar */}
        <div className="w-1/3 flex flex-col border-r border-slate-800 pr-4">
          <div className="flex flex-wrap gap-2 mb-4">
            {(['Urgent', 'Needs Response', 'FYI', 'Spam', 'Drafts'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => { setActiveTab(tab); setSelectedEmail(null); }}
                className={`px-2 py-1 border rounded ${activeTab === tab ? 'bg-slate-800 text-accent-400 border-accent-400' : 'border-slate-700 text-slate-400 hover:border-slate-500'}`}
              >
                {tab}
              </button>
            ))}
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-2 pr-2">
            {activeTab !== 'Drafts' ? (
              inbox.map(email => (
                <div 
                  key={email.id} 
                  onClick={() => setSelectedEmail(email)}
                  className={`p-2 cursor-pointer border ${selectedEmail?.id === email.id ? 'border-accent-400 bg-slate-800/50' : 'border-slate-800 bg-slate-800/20 hover:border-slate-600'}`}
                >
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="font-bold truncate">{email.from}</span>
                    <span className="text-[10px] text-slate-500">{new Date(email.date).toLocaleDateString()}</span>
                  </div>
                  <div className="truncate text-slate-400">{email.subject}</div>
                </div>
              ))
            ) : (
              drafts.map(draft => (
                <div key={draft.id} className="p-2 border border-slate-800 bg-slate-800/20">
                  <div className="text-accent-400 mb-1">Draft for Email: {draft.emailId}</div>
                  <div className="truncate text-slate-400 mb-2">{draft.body}</div>
                  {draft.guardianScreened && (
                    <div className="text-[10px] text-green-400 border border-green-400/30 inline-block px-1 mb-2">
                      Screened by Guardian Engine
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button onClick={() => handleApproveDraft(draft.id)} className="px-2 py-1 bg-slate-800 text-green-400 border border-green-900 hover:bg-slate-700">Approve Draft</button>
                    <button onClick={() => handleRejectDraft(draft.id)} className="px-2 py-1 bg-slate-800 text-red-400 border border-red-900 hover:bg-slate-700">Reject Draft</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="w-2/3 flex flex-col pl-2">
          {selectedEmail ? (
            <div className="flex flex-col h-full bg-slate-800/10 p-4 border border-slate-800">
              <div className="border-b border-slate-800 pb-4 mb-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg text-accent-400">{selectedEmail.subject}</h3>
                  <span className="px-2 py-1 border border-slate-700 bg-slate-800 text-[10px]">{selectedEmail.priority}</span>
                </div>
                <div className="text-slate-400">From: <span className="text-cyber-cyan">{selectedEmail.from}</span></div>
                <div className="text-slate-400">Date: {new Date(selectedEmail.date).toLocaleString()}</div>
              </div>
              <div className="flex-1 overflow-y-auto text-slate-300 whitespace-pre-wrap mb-4">
                {selectedEmail.body}
              </div>
              <div className="border-t border-slate-800 pt-4 mt-auto">
                <button 
                  onClick={() => generateDraft(selectedEmail.id)}
                  className="px-4 py-2 bg-slate-800 text-accent-400 border border-accent-400 hover:bg-slate-700 uppercase tracking-widest"
                >
                  Generate Draft Reply
                </button>
              </div>
            </div>
          ) : activeTab !== 'Drafts' ? (
            <div className="flex-1 flex items-center justify-center text-slate-600 uppercase tracking-widest border border-slate-800/50 border-dashed">
              [ NO COMM LINK SELECTED ]
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-600 uppercase tracking-widest border border-slate-800/50 border-dashed">
              [ DRAFTS REVIEW QUEUE ]
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
