import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import Chat from './Chat';
import Payment from './Payment';

function App() {
  const [session, setSession] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => setSession(session));
    return () => listener?.unsubscribe();
  }, []);

  if (!session) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <h1>VibeCode AI</h1>
        <button onClick={() => supabase.auth.signInWithOAuth({ provider: 'github' })}>
          Login with GitHub
        </button>
        <button onClick={() => supabase.auth.signInWithOAuth({ provider: 'google' })}>
          Login with Google
        </button>
      </div>
    );
  }

  return (
    <div>
      <Chat user={session.user} />
      <Payment user={session.user} />
    </div>
  );
}

export default App;
