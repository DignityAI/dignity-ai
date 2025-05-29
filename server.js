// server.js - Dignity AI Backend
const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(',') : true
}));
app.use(express.json({ limit: '10mb' }));

// Rate limiting - 30 requests per minute per IP
const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30,
  message: { error: 'Too many requests, please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// Dignity Lens Framework Content
const DIGNITY_FRAMEWORK = `You are Dignity AI, an advanced AI system developed by the Defy Racism Collective that analyzes systematic racism through the revolutionary Dignity Lens framework.

THE DIGNITY LENS FRAMEWORK:
The Dignity Lens examines systematic racism through 4 interconnected domains across 7 historical eras:

THE 4 DOMAINS:
1. POWER STRUCTURES - Who controls decisions and resources
2. CONTROL MECHANISMS - How communities are contained and suppressed  
3. COMMUNITY RESISTANCE - How communities survive and fight back
4. LIBERATION STRATEGIES - What actually works to build freedom and power

THE 7 HISTORICAL ERAS:
1. Enslavement & Early Resistance (1600s-1865)
2. Reconstruction & Backlash (1865-1910)
3. Jim Crow & Black Institution-Building (1910-1950)
4. Civil Rights & Black Power (1950-1975)
5. Neoliberalization & Mass Incarceration (1975-2008)
6. Digital Rebellion & Corporate Capture (2008-2020)
7. Abolitionist Futuring & AI Counterinsurgency (2020-Present)

CORE PRINCIPLES:
- Connect individual experiences to systematic patterns
- Address root causes, not just symptoms
- Center community control and self-determination
- Build cross-racial solidarity while respecting community leadership
- Focus on liberation strategies that build lasting community power
- Always provide concrete organizing opportunities, especially in Chicago

RESPONSE STRUCTURE:
1. Acknowledge the question with dignity and respect
2. Apply relevant Dignity Lens domains to analyze the issue
3. Connect to historical patterns across eras
4. Explain current manifestations and systematic functions
5. Highlight community resistance and successful organizing
6. Provide specific liberation strategies and organizing opportunities
7. Include concrete Chicago organizing opportunities when possible

Your responses should be sophisticated yet accessible, revolutionary yet practical, analytical yet hopeful. Always end with actionable steps for community organizing and systemic change.`;

// Usage tracking
const usageStats = {
  totalRequests: 0,
  totalTokens: 0,
  dailyRequests: 0,
  lastReset: new Date().toDateString(),
  errors: 0
};

// Reset daily counter
function resetDailyStats() {
  const today = new Date().toDateString();
  if (usageStats.lastReset !== today) {
    usageStats.dailyRequests = 0;
    usageStats.lastReset = today;
  }
}

// Input validation
function validateQuestion(question) {
  if (!question || typeof question !== 'string') {
    return { valid: false, error: 'Question is required and must be text.' };
  }
  
  const trimmed = question.trim();
  if (trimmed.length === 0) {
    return { valid: false, error: 'Please provide a question about systematic racism.' };
  }
  
  if (trimmed.length > 1000) {
    return { valid: false, error: 'Question too long. Please keep it under 1000 characters.' };
  }
  
  return { valid: true, question: trimmed };
}

// Main API endpoint
app.post('/api/analyze', async (req, res) => {
  try {
    resetDailyStats();
    
    const validation = validateQuestion(req.body.question);
    if (!validation.valid) {
      return res.status(400).json({ error: validation.error });
    }

    const question = validation.question;

    // Check if we have API key
    if (!process.env.ANTHROPIC_API_KEY) {
      console.error('Missing ANTHROPIC_API_KEY environment variable');
      return res.status(500).json({ 
        error: 'Server configuration error. Please contact administrator.' 
      });
    }

    // Call Claude API
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-3-5-haiku-20241022',
        max_tokens: 1500,
        temperature: 0.7,
        system: DIGNITY_FRAMEWORK,
        messages: [{
          role: 'user',
          content: question
        }]
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Claude API Error:', response.status, errorData);
      
      usageStats.errors++;
      
      if (response.status === 429) {
        return res.status(429).json({ 
          error: 'API rate limit reached. Please try again in a moment.' 
        });
      }
      
      if (response.status === 401) {
        return res.status(500).json({ 
          error: 'Authentication error. Please contact administrator.' 
        });
      }
      
      return res.status(500).json({ 
        error: 'Analysis temporarily unavailable. Please try again.' 
      });
    }

    const data = await response.json();
    const analysis = data.content[0].text;

    // Update usage stats
    usageStats.totalRequests++;
    usageStats.dailyRequests++;
    usageStats.totalTokens += (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0);

    // Log usage for monitoring
    console.log(`✅ Request ${usageStats.totalRequests}: ${data.usage?.input_tokens || 0} input + ${data.usage?.output_tokens || 0} output tokens`);

    res.json({ 
      analysis,
      usage: {
        daily_requests: usageStats.dailyRequests,
        total_requests: usageStats.totalRequests,
        input_tokens: data.usage?.input_tokens || 0,
        output_tokens: data.usage?.output_tokens || 0
      }
    });

  } catch (error) {
    console.error('Server Error:', error);
    usageStats.errors++;
    res.status(500).json({ 
      error: 'Internal server error. Please try again.' 
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  resetDailyStats();
  res.json({
    status: 'healthy',
    uptime: Math.floor(process.uptime()),
    usage: usageStats,
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Dignity AI Backend Server',
    status: 'running',
    endpoints: {
      analyze: 'POST /api/analyze',
      health: 'GET /api/health'
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled Error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

app.listen(port, () => {
  console.log(`🚀 Dignity AI server running on port ${port}`);
  console.log(`📊 Health check: http://localhost:${port}/api/health`);
  console.log(`🔧 API endpoint: http://localhost:${port}/api/analyze`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
});

module.exports = app;
