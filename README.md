# GenAI-Powered Secure Code Review Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

**A hybrid SAST + LLM system that reduces false positives by 80-90% while maintaining high security coverage.**

## 🎯 Overview

This project implements a production-ready security code review bot that combines:
- **High Recall**: SAST tools (Bandit, ESLint) catch all potential vulnerabilities
- **High Precision**: LLM (GPT-4) filters false positives using semantic understanding
- **Privacy-First**: Microsoft Presidio ensures no PII/secrets reach external APIs
- **Automated**: GitHub webhooks trigger scans and post inline PR comments

### The Problem

Traditional SAST tools have **50-90% false positive rates**, causing:
- Alert fatigue for developers
- Ignored security warnings
- Wasted time investigating non-issues

### The Solution

**Hybrid Architecture**: SAST for exhaustive coverage + LLM for intelligent filtering

```
SAST (High Recall)  →  LLM (High Precision)  →  True Positives Only
   ~50-90% FP              ~5-10% FP              Actionable Results
```

## ✨ Key Features

- **🔍 Dual SAST Integration**: Bandit (Python) + ESLint (JavaScript)
- **🤖 LLM Verification**: OpenAI GPT-4 with structured outputs (guaranteed JSON parsing)
- **🔒 Privacy Firewall**: Presidio PII detection + custom secret redaction
- **🌳 Smart Context Extraction**: Tree-sitter for function/class-aware context
- **🔗 GitHub Integration**: Webhook-triggered scans with inline PR comments
- **📊 Production Ready**: Docker Compose, Celery workers, PostgreSQL persistence
- **💰 Cost Effective**: ~$0.01-0.02 per PR scan

## 🏗️ Architecture

```
┌─────────────────┐
│  GitHub PR      │
└────────┬────────┘
         │ webhook
    ┌────▼─────────────┐
    │  FastAPI Server  │
    └────┬─────────────┘
         │ queue
    ┌────▼─────────────┐
    │  Celery Worker   │
    └────┬─────────────┘
         │
    ┌────▼─────────────┐
    │  SAST Scan       │ ← Bandit + ESLint
    │  (High Recall)   │
    └────┬─────────────┘
         │
    ┌────▼─────────────┐
    │  Context Extract │ ← Tree-sitter
    │  (Function/Class)│
    └────┬─────────────┘
         │
    ┌────▼─────────────┐
    │  Privacy Filter  │ ← Presidio
    │  (PII/Secrets)   │
    └────┬─────────────┘
         │
    ┌────▼─────────────┐
    │  LLM Verify      │ ← GPT-4
    │  (High Precision)│
    └────┬─────────────┘
         │
    ┌────▼─────────────┐
    │  PR Comment      │ ← GitHub API
    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key
- GitHub Personal Access Token

### 1. Clone Repository
```bash
git clone https://github.com/jitesh523/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot.git
cd A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```bash
OPENAI_API_KEY=sk-your-openai-key
GITHUB_TOKEN=ghp_your-github-token
GITHUB_WEBHOOK_SECRET=your-random-secret
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify
```bash
curl http://localhost:8000/health
MIT

## References

Based on research from:
- [LLM-Driven SAST-Genius](https://arxiv.org/abs/2509.15433)
- [OWASP Top 10](https://owasp.org/Top10/2021/)
