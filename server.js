const express = require('express');
const fetch = require('node-fetch');
const fs = require('fs');

// Simple .env loader
try {
  const envContent = fs.readFileSync('.env', 'utf8');
  envContent.split('\n').forEach(line => {
    const [key, ...rest] = line.split('=');
    if (key && rest.length) process.env[key.trim()] = rest.join('=').trim();
  });
} catch (e) { }

const app = express();
app.use(express.json({ limit: '50mb' }));
app.use(express.static('.'));

// Model auto-discovery
let availableModels = [];
async function discoverModels() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return;
  try {
    const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
    const data = await resp.json();
    if (data.models) {
      availableModels = data.models.map(m => m.name.replace('models/', ''));
      console.log('--- Found available Gemini models ---');
      console.log(availableModels.join(', '));
    }
  } catch (e) {
    console.error('Error discovering models:', e.message);
  }
}
discoverModels();

// GEMINI PROXY (Smart Model Pick)
app.post('/api/gemini', async (req, res) => {
  console.log('--- Outgoing Request to Gemini ---');
  try {
    const apiKey = process.env.GEMINI_API_KEY;
    // Auto-pick best available if current fails
    let model = req.body.model || 'gemini-1.5-flash';
    if (availableModels.length && !availableModels.includes(model)) {
      model = availableModels.find(m => m.includes('flash')) || availableModels.find(m => m.includes('pro')) || availableModels[0];
      console.log(`Fallback: Using discovered model "${model}" instead.`);
    }

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body.payload)
    });

    const data = await response.json();
    if (!response.ok) {
      console.error(`Gemini API Error:`, data);
      return res.status(response.status).json(data);
    }
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});



// AADHAAR eKYC — Step 1: Send OTP
app.post('/api/aadhaar/otp', async (req, res) => {
  console.log('--- Aadhaar OTP Request ---');
  try {
    const response = await fetch('http://localhost:8000/aadhaar/otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    if (!response.ok) return res.status(response.status).json(data);
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: 'eKYC Engine Offline', message: 'Start brain.py on port 8000.' });
  }
});

// AADHAAR eKYC — Step 2: Verify OTP
app.post('/api/aadhaar/verify', async (req, res) => {
  console.log('--- Aadhaar OTP Verify ---');
  try {
    const response = await fetch('http://localhost:8000/aadhaar/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    if (!response.ok) return res.status(response.status).json(data);
    res.json(data);
  } catch (err) {
    res.status(503).json({ error: 'eKYC Engine Offline', message: 'Start brain.py on port 8000.' });
  }
});

// PYTHON BRAIN PROXY - THE REASONING ENGINE
app.post('/api/oracle', async (req, res) => {
  console.log('--- Consulting Python Brain ---');
  try {
    const response = await fetch('http://localhost:8000/analyze_intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    if (!response.ok) {
        console.error('Python Brain Error:', data);
        return res.status(response.status).json(data);
    }
    res.json(data);
  } catch (err) {
    console.error('Python Brain Offline:', err.message);
    res.status(503).json({ error: "Intelligence Engine Offline", message: "Start the Python brain.py server on port 8000." });
  }
});

// AI PROFIT PROJECTION AGENT PROXY
app.post('/api/roi-prediction', async (req, res) => {
  try {
    const response = await fetch('http://localhost:8000/predict_roi', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    res.json(await response.json());
  } catch (err) {
    res.status(503).json({ error: "ROI Agent Offline" });
  }
});

app.listen(3000, () => console.log('Running at http://localhost:3000'));
