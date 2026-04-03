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
} catch (e) {}

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

// CLAUDE PROXY
app.post('/api/claude', async (req, res) => {
  console.log('--- Outgoing Request to Anthropic ---');
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    if (!response.ok) return res.status(response.status).json(data);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(3000, () => console.log('Running at http://localhost:3000'));