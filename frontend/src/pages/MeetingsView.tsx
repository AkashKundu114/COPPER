import React, { useState, useEffect, useRef } from 'react';
import { meetingsAPI } from '../services/api';

// Types for meeting data
interface Meeting {
  id: string;
  title: string;
  status: 'recording' | 'processing' | 'completed';
  duration?: number;
  created_at: string;
  transcription?: string;
}

interface MeetingNotes {
  executive_summary: string;
  key_decisions: string[];
  open_questions: string[];
  important_quotes: string[];
}

interface Task {
  id: string;
  description: string;
  status: string;
}

export const MeetingsView: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [notes, setNotes] = useState<MeetingNotes | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  
  const [isRecording, setIsRecording] = useState(false);
  const [activeMeetingId, setActiveMeetingId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      const res = await meetingsAPI.list();
      setMeetings(res.data.meetings || res.data); // Adjust depending on actual API response
    } catch (err) {
      console.error("Failed to fetch meetings", err);
    }
  };

  const loadMeetingDetails = async (meeting: Meeting) => {
    setSelectedMeeting(meeting);
    setNotes(null);
    setTasks([]);
    try {
      const [fullRes, notesRes, tasksRes] = await Promise.all([
        meetingsAPI.get(meeting.id),
        meetingsAPI.getNotes(meeting.id),
        meetingsAPI.getTasks(meeting.id)
      ]);
      setSelectedMeeting(fullRes.data);
      setNotes(notesRes.data);
      setTasks(tasksRes.data.tasks || tasksRes.data);
    } catch (err) {
      console.error("Failed to load details", err);
    }
  };

  const startMeeting = async () => {
    try {
      // Start API
      const res = await meetingsAPI.start(newTitle);
      const meetingId = res.data.id;
      setActiveMeetingId(meetingId);
      setIsRecording(true);
      setNewTitle('');

      // Start local mic stream (simulated / basic MediaRecorder)
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        mediaRecorderRef.current.start(1000); // 1-second chunks
        // Ideally, we'd stream this data to backend via WebSocket or POST chunks
      }

      fetchMeetings();
    } catch (err) {
      console.error("Failed to start meeting", err);
    }
  };

  const stopMeeting = async () => {
    if (!activeMeetingId) return;
    try {
      await meetingsAPI.stop(activeMeetingId);
      setIsRecording(false);
      setActiveMeetingId(null);

      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
        mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
      }

      fetchMeetings();
    } catch (err) {
      console.error("Failed to stop meeting", err);
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex h-full w-full bg-slate-900/80 text-verdigris font-mono text-xs overflow-hidden">
      {/* Left panel: History & Controls */}
      <div className="w-1/3 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-lg text-accent-400 mb-4 uppercase tracking-widest">Meeting Intel</h2>
          
          <div className="flex flex-col gap-2 mb-4">
            <input 
              type="text"
              placeholder="Meeting Title..."
              className="bg-slate-800 border border-slate-700 p-2 text-verdigris focus:outline-none focus:border-accent-400"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              disabled={isRecording}
            />
            {isRecording ? (
              <button 
                onClick={stopMeeting}
                className="bg-red-900/50 hover:bg-red-800/80 text-red-400 border border-red-800 p-2 uppercase tracking-widest transition-colors flex justify-center items-center gap-2"
              >
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                Stop Recording
              </button>
            ) : (
              <button 
                onClick={startMeeting}
                className="bg-slate-800 hover:bg-slate-700 text-accent-400 border border-slate-700 p-2 uppercase tracking-widest transition-colors"
              >
                Start Recording
              </button>
            )}
          </div>
          
          {isRecording && (
            <div className="text-accent-400 text-[10px] animate-pulse">
              [SYSTEM] Streaming local audio to C.O.P.P.E.R. core...
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <h3 className="mb-3 text-slate-400 uppercase">Archive</h3>
          <div className="flex flex-col gap-2">
            {meetings.map(m => (
              <div 
                key={m.id} 
                onClick={() => loadMeetingDetails(m)}
                className={`p-3 border cursor-pointer transition-colors ${
                  selectedMeeting?.id === m.id 
                    ? 'border-accent-400 bg-slate-800/50' 
                    : 'border-slate-800 hover:border-slate-600 bg-slate-900/50'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <div className="font-bold text-accent-400 truncate pr-2">{m.title}</div>
                  <div className={`text-[10px] px-1 py-0.5 rounded ${
                    m.status === 'recording' ? 'bg-red-900/50 text-red-400 border border-red-800 animate-pulse' :
                    m.status === 'processing' ? 'bg-yellow-900/50 text-yellow-400 border border-yellow-800' :
                    'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}>
                    {m.status.toUpperCase()}
                  </div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>{new Date(m.created_at).toLocaleDateString()}</span>
                  <span>{formatDuration(m.duration)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel: Details */}
      <div className="w-2/3 flex flex-col p-6 overflow-y-auto custom-scrollbar">
        {selectedMeeting ? (
          <div className="max-w-3xl w-full mx-auto space-y-6">
            
            {/* Header */}
            <div className="border-b border-slate-800 pb-4">
              <h1 className="text-2xl text-accent-400 mb-2">{selectedMeeting.title}</h1>
              <div className="flex gap-4 text-slate-500">
                <span>ID: {selectedMeeting.id}</span>
                <span>DATE: {new Date(selectedMeeting.created_at).toLocaleString()}</span>
                <span>STATUS: {selectedMeeting.status.toUpperCase()}</span>
              </div>
            </div>

            {/* Notes Section */}
            {notes && (
              <div className="border border-slate-800 bg-slate-900/50 p-4">
                <h3 className="text-accent-400 border-b border-slate-800 pb-2 mb-4 uppercase">Structured Synthesis</h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="text-slate-400 mb-1 font-bold">Executive Summary</div>
                    <div className="text-slate-300 leading-relaxed">{notes.executive_summary}</div>
                  </div>

                  {notes.key_decisions && notes.key_decisions.length > 0 && (
                    <div>
                      <div className="text-slate-400 mb-1 font-bold">Key Decisions</div>
                      <ul className="list-disc pl-4 space-y-1 text-accent-400/80">
                        {notes.key_decisions.map((dec, i) => <li key={i}>{dec}</li>)}
                      </ul>
                    </div>
                  )}

                  {notes.open_questions && notes.open_questions.length > 0 && (
                    <div>
                      <div className="text-slate-400 mb-1 font-bold">Open Questions</div>
                      <ul className="list-disc pl-4 space-y-1 text-yellow-400/80">
                        {notes.open_questions.map((q, i) => <li key={i}>{q}</li>)}
                      </ul>
                    </div>
                  )}

                  {notes.important_quotes && notes.important_quotes.length > 0 && (
                    <div>
                      <div className="text-slate-400 mb-1 font-bold">Important Quotes</div>
                      <div className="space-y-2">
                        {notes.important_quotes.map((q, i) => (
                          <div key={i} className="pl-3 border-l-2 border-slate-700 italic text-slate-400">
                            "{q}"
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Items */}
            {tasks && tasks.length > 0 && (
              <div className="border border-slate-800 bg-slate-900/50 p-4">
                <h3 className="text-accent-400 border-b border-slate-800 pb-2 mb-4 uppercase">Action Items & Tasks</h3>
                <div className="space-y-2">
                  {tasks.map(t => (
                    <div key={t.id} className="flex items-center gap-3 bg-slate-800/30 p-2 border border-slate-800">
                      <div className="w-3 h-3 border border-accent-400 rounded-sm"></div>
                      <span className="flex-1">{t.description}</span>
                      <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-1 uppercase">{t.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Full Transcription */}
            {selectedMeeting.transcription && (
              <div className="border border-slate-800 bg-slate-900/50 p-4">
                <h3 className="text-accent-400 border-b border-slate-800 pb-2 mb-4 uppercase">Raw Transcription Log</h3>
                <div className="whitespace-pre-wrap text-slate-400 leading-relaxed max-h-96 overflow-y-auto custom-scrollbar pr-2">
                  {selectedMeeting.transcription}
                </div>
              </div>
            )}

          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-600 uppercase tracking-widest">
            Select a meeting to view intelligence
          </div>
        )}
      </div>
    </div>
  );
};
