import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { supabase } from './supabaseClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Chat({ user }) {
  const [msg, setMsg] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [points, setPoints] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPoints();
  }, []);

  const fetchPoints = async () => {
    const res = await axios.get(`${API_URL}/user-points/${user.id}`);
    setPoints(res.data.points || 0);
  };

  const send = async () => {
    if (!msg.trim()) return;
    if (points < 1) {
      alert('Insufficient points. Buy more!');
      return;
    }
    setLoading(true);
    setChatLog([...chatLog, { sender: 'user', content: msg }]);
    
    try {
      const res = await axios.post(`${API_URL}/vibe`, {
        user_id: user.id,
        message: msg,
        project_id: projectId
      });
      
      if (res.data.error) {
        alert(res.data.error);
        setLoading(false);
        return;
      }
      
      setChatLog([...chatLog, { sender: 'user', content: msg }, { sender: 'ai', content: res.data.reply }]);
      setPoints(res.data.remaining_points);
      if (res.data.project_id) setProjectId(res.data.project_id);
    } catch (err) {
      alert('Error: ' + err.message);
    }
    setMsg('');
    setLoading(false);
  };

  return (
    <div style={{ padding: 20, maxWidth: 800, margin: '0 auto' }}>
      <h2>VibeCode AI</h2>
      <p>Points remaining: <strong>{points}</strong></p>
      <div style={{ height: 400, overflowY: 'scroll', border: '1px solid #ccc', padding: 10, marginBottom: 10 }}>
        {chatLog.map((c, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <b>{c.sender === 'user' ? 'You' : 'AI'}:</b>
            <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 10 }}>{c.content}</pre>
          </div>
        ))}
      </div>
      <input 
        value={msg} 
        onChange={e => setMsg(e.target.value)} 
        placeholder="Describe your app..." 
        style={{ width: '70%', padding: 10 }}
        disabled={loading}
      />
      <button onClick={send} disabled={loading || points < 1} style={{ padding: 10, marginLeft: 10 }}>
        {loading ? 'Generating...' : 'Send'}
      </button>
    </div>
  );
                                       }
