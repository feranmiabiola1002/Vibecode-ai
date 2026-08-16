import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Payment({ user }) {
  const [loading, setLoading] = useState(false);

  const handlePayment = async (plan) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/init-payment`, {
        user_id: user.id,
        email: user.email,
        plan: plan
      });
      if (res.data.status) {
        window.location.href = res.data.data.authorization_url;
      } else {
        alert('Payment initialization failed');
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 20, borderTop: '1px solid #ccc', marginTop: 20 }}>
      <h3>Buy More Points</h3>
      <button 
        onClick={() => handlePayment('premium')} 
        disabled={loading}
        style={{ marginRight: 10, padding: 10 }}
      >
        Premium – ₦1,500 (10.5 points)
      </button>
      <button 
        onClick={() => handlePayment('pro')} 
        disabled={loading}
        style={{ padding: 10 }}
      >
        Pro – ₦3,000 (25 points)
      </button>
      <p style={{ fontSize: 12, color: '#666' }}>Free users get 5 points on signup</p>
    </div>
  );
        }
