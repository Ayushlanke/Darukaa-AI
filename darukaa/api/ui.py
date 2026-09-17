HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Darukaa.Earth — AI Biodiversity Intelligence</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-darkest: #071510;
      --bg-sidebar: #0a1f17;
      --bg-chat: #0d281e;
      --bg-card: rgba(18, 48, 37, 0.85);
      --bg-card-hover: rgba(24, 62, 48, 0.95);
      --bg-user-msg: linear-gradient(135deg, #065f46 0%, #047857 100%);
      --border-color: rgba(52, 211, 153, 0.15);
      --border-hover: rgba(52, 211, 153, 0.4);
      --text-main: #f0fdf4;
      --text-muted: #86efac;
      --text-subtle: #94a3b8;
      --accent-emerald: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.25);
      --accent-amber: #f59e0b;
      --accent-blue: #38bdf8;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-sans);
      background-color: var(--bg-chat);
      background-image: 
        radial-gradient(at 15% 15%, rgba(16, 185, 129, 0.08) 0px, transparent 50%),
        radial-gradient(at 85% 85%, rgba(5, 150, 105, 0.06) 0px, transparent 50%);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Sidebar - ChatGPT style */
    aside {
      width: 270px;
      background: var(--bg-sidebar);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }

    .sidebar-top {
      padding: 16px 14px 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      border-bottom: 1px solid var(--border-color);
    }

    .brand-block {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .brand-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, #10b981 0%, #047857 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-weight: 700;
      font-size: 16px;
      box-shadow: 0 0 14px var(--accent-glow);
    }

    .brand-title {
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      background: linear-gradient(90deg, #ecfdf5, #a7f3d0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
      opacity: 0.85;
    }

    .btn-new-chat {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #ecfdf5;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 0.86rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }

    .btn-new-chat:hover {
      background: rgba(16, 185, 129, 0.22);
      border-color: var(--accent-emerald);
      box-shadow: 0 0 12px var(--accent-glow);
    }

    .sidebar-history-label {
      padding: 12px 14px 4px;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
      font-weight: 600;
    }

    .sidebar-chats {
      flex: 1;
      overflow-y: auto;
      padding: 4px 8px;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }

    .history-item {
      padding: 9px 12px;
      border-radius: 8px;
      color: var(--text-subtle);
      font-size: 0.84rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      transition: all 0.15s;
    }

    .history-item:hover, .history-item.active {
      background: rgba(255, 255, 255, 0.06);
      color: var(--text-main);
    }

    .history-item-title {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }

    .history-delete-btn {
      opacity: 0;
      color: var(--text-subtle);
      font-size: 12px;
      padding: 2px 4px;
      border-radius: 4px;
      transition: opacity 0.15s;
    }

    .history-item:hover .history-delete-btn {
      opacity: 0.7;
    }

    .history-delete-btn:hover {
      opacity: 1;
      color: #fca5a5;
    }

    .sidebar-footer {
      padding: 14px 16px;
      border-top: 1px solid var(--border-color);
      background: rgba(0, 0, 0, 0.2);
      font-size: 0.74rem;
      color: var(--text-subtle);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .system-status {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #a7f3d0;
      font-size: 0.78rem;
      font-family: var(--font-mono);
    }

    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 10px #10b981;
    }

    /* Main Container */
    .main-workspace {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      position: relative;
    }

    .top-header {
      height: 54px;
      padding: 0 24px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(13, 40, 30, 0.75);
      backdrop-filter: blur(12px);
      flex-shrink: 0;
      z-index: 10;
    }

    .header-context {
      font-size: 0.88rem;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 500;
    }

    .header-pill {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 3px 9px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-family: var(--font-mono);
      color: #6ee7b7;
    }

    .header-links {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .btn-header {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-header:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--border-hover);
    }

    /* Chat Stream */
    .chat-scroll-area {
      flex: 1;
      overflow-y: auto;
      padding: 24px 20px;
      display: flex;
      flex-direction: column;
    }

    .chat-flow {
      max-width: 820px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 22px;
    }

    /* Hero / Empty Screen */
    .hero-container {
      margin: auto 0;
      padding: 30px 0;
      text-align: center;
    }

    .hero-badge {
      display: inline-block;
      padding: 5px 12px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.35);
      border-radius: 20px;
      color: #6ee7b7;
      font-size: 0.78rem;
      font-weight: 600;
      margin-bottom: 14px;
      letter-spacing: 0.02em;
    }

    .hero-title {
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(90deg, #ecfdf5, #6ee7b7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 10px;
    }

    .hero-description {
      color: var(--text-subtle);
      font-size: 0.94rem;
      line-height: 1.6;
      max-width: 620px;
      margin: 0 auto 28px;
    }

    .prompt-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      text-align: left;
    }

    @media (max-width: 700px) {
      .prompt-grid { grid-template-columns: 1fr; }
    }

    .prompt-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 14px 16px;
      cursor: pointer;
      backdrop-filter: blur(8px);
      transition: all 0.2s;
    }

    .prompt-card:hover {
      background: var(--bg-card-hover);
      border-color: var(--accent-emerald);
      box-shadow: 0 4px 20px var(--accent-glow);
      transform: translateY(-2px);
    }

    .prompt-card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }

    .prompt-card-icon {
      font-size: 16px;
    }

    .prompt-card-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: #ecfdf5;
    }

    .prompt-card-desc {
      font-size: 0.78rem;
      color: var(--text-subtle);
      line-height: 1.4;
    }

    /* Message Rows */
    .chat-row {
      display: flex;
      gap: 14px;
      width: 100%;
      animation: messageIn 0.25s ease-out;
    }

    @keyframes messageIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .chat-row.user {
      justify-content: flex-end;
    }

    .chat-avatar {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      flex-shrink: 0;
      margin-top: 2px;
    }

    .chat-avatar.ai {
      background: linear-gradient(135deg, #059669 0%, #022c22 100%);
      border: 1px solid rgba(52, 211, 153, 0.4);
      color: #ecfdf5;
    }

    .chat-bubble {
      max-width: 86%;
      font-size: 0.93rem;
      line-height: 1.6;
    }

    .chat-row.user .chat-bubble {
      background: var(--bg-user-msg);
      border: 1px solid rgba(52, 211, 153, 0.35);
      color: #ffffff;
      padding: 12px 18px;
      border-radius: 14px;
      border-bottom-right-radius: 3px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    .chat-row.ai .chat-bubble {
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      border-bottom-left-radius: 4px;
      padding: 18px 20px;
      color: var(--text-main);
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
    }

    /* AI Response Components */
    .intervention-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-color);
    }

    .intervention-title {
      font-size: 1.12rem;
      font-weight: 700;
      color: #ecfdf5;
      line-height: 1.4;
    }

    .tag-group {
      display: flex;
      gap: 6px;
      flex-shrink: 0;
    }

    .pill-tag {
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      padding: 4px 9px;
      border-radius: 999px;
      letter-spacing: 0.05em;
    }

    .pill-confidence { background: rgba(16, 185, 129, 0.18); color: #6ee7b7; border: 1px solid #10b981; }
    .pill-horizon { background: rgba(56, 189, 248, 0.18); color: #7dd3fc; border: 1px solid #38bdf8; }

    .narrative-body {
      font-size: 0.95rem;
      line-height: 1.65;
      color: #e2e8f0;
      margin-bottom: 14px;
    }

    .meta-section-heading {
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 6px;
    }

    .meta-pills-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 14px;
    }

    .code-pill {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-color);
      font-family: var(--font-mono);
      font-size: 0.76rem;
      padding: 3px 9px;
      border-radius: 6px;
      color: #a7f3d0;
    }

    .citations-card {
      background: rgba(0, 0, 0, 0.25);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 10px 14px;
      margin-bottom: 12px;
    }

    .citation-entry {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      padding: 6px 0;
      font-size: 0.8rem;
      border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
    }
    .citation-entry:last-child { border-bottom: none; }

    .citation-source { color: #cbd5e1; }
    .citation-badge {
      font-size: 0.7rem;
      font-family: var(--font-mono);
      color: #34d399;
      background: rgba(52, 211, 153, 0.12);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .limitations-box {
      font-size: 0.8rem;
      color: var(--text-subtle);
      border-left: 2px solid var(--accent-amber);
      padding-left: 10px;
      margin: 8px 0 14px;
    }

    .clarification-callout {
      background: rgba(245, 158, 11, 0.09);
      border: 1px solid rgba(245, 158, 11, 0.35);
      border-radius: 10px;
      padding: 15px 18px;
    }

    .clarification-callout .head {
      font-size: 0.84rem;
      font-weight: 600;
      color: #fde68a;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .clarification-callout .content {
      font-size: 0.93rem;
      line-height: 1.55;
      color: #fef08a;
    }

    /* Dedicated User-Facing Red API Error Alert Card */
    .api-error-card {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(185, 28, 28, 0.22) 100%);
      border: 1px solid rgba(239, 68, 68, 0.45);
      border-radius: 12px;
      padding: 18px 20px;
      box-shadow: 0 8px 30px rgba(220, 38, 38, 0.22), inset 0 1px 1px rgba(255, 255, 255, 0.1);
      color: #fecaca;
      position: relative;
      overflow: hidden;
      width: 100%;
    }

    .api-error-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: #ef4444;
      box-shadow: 0 0 10px #ef4444;
    }

    .api-error-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(239, 68, 68, 0.25);
    }

    .api-error-title-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .api-error-icon-box {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: rgba(239, 68, 68, 0.22);
      border: 1px solid rgba(239, 68, 68, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      flex-shrink: 0;
      animation: alertPulse 2s infinite ease-in-out;
    }

    @keyframes alertPulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
      50% { box-shadow: 0 0 10px 3px rgba(239, 68, 68, 0.35); }
    }

    .api-error-title {
      font-size: 0.98rem;
      font-weight: 700;
      color: #fee2e2;
      letter-spacing: -0.01em;
    }

    .api-error-badge {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 3px 9px;
      border-radius: 6px;
      background: rgba(239, 68, 68, 0.25);
      border: 1px solid rgba(239, 68, 68, 0.55);
      color: #fca5a5;
    }

    .api-error-message {
      font-size: 0.93rem;
      line-height: 1.6;
      color: #fca5a5;
      margin-bottom: 0;
    }

    .followups-block {
      border-top: 1px solid var(--border-color);
      padding-top: 12px;
      margin-top: 10px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .followup-btn {
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.25);
      color: #a7f3d0;
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 0.82rem;
      text-align: left;
      cursor: pointer;
      transition: all 0.2s;
    }

    .followup-btn:hover {
      background: rgba(16, 185, 129, 0.18);
      border-color: var(--accent-emerald);
      transform: translateX(3px);
    }

    /* In-stream Thinking Animation */
    .thinking-row {
      display: flex;
      gap: 14px;
      width: 100%;
      animation: messageIn 0.25s ease-out;
    }

    .thinking-bubble {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 320px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .typing-dots {
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .typing-dots span {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulseDot 1.4s infinite ease-in-out both;
    }

    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }

    @keyframes pulseDot {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.3; }
      40% { transform: scale(1.1); opacity: 1; }
    }

    .thinking-label {
      font-size: 0.84rem;
      color: var(--text-muted);
    }

    /* Input Dock - Floating ChatGPT Style */
    .input-dock {
      padding: 14px 24px 20px;
      background: linear-gradient(180deg, transparent 0%, var(--bg-chat) 40%);
      flex-shrink: 0;
    }

    .input-form {
      max-width: 820px;
      margin: 0 auto;
      background: rgba(18, 48, 37, 0.9);
      border: 1px solid var(--border-hover);
      border-radius: 16px;
      padding: 12px 16px;
      display: flex;
      align-items: flex-end;
      gap: 12px;
      box-shadow: 0 10px 32px rgba(0, 0, 0, 0.4);
      backdrop-filter: blur(16px);
      transition: all 0.2s;
    }

    .input-form:focus-within {
      border-color: var(--accent-emerald);
      box-shadow: 0 0 24px var(--accent-glow);
    }

    textarea.main-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #ffffff;
      font-family: var(--font-sans);
      font-size: 0.95rem;
      line-height: 1.5;
      resize: none;
      max-height: 140px;
      min-height: 24px;
    }

    textarea.main-input::placeholder {
      color: var(--text-subtle);
      opacity: 0.8;
    }

    .btn-send {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      border: none;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.2s;
    }

    .btn-send:hover:not(:disabled) {
      box-shadow: 0 0 15px var(--accent-glow);
      transform: scale(1.05);
    }

    .btn-send:disabled {
      background: rgba(255, 255, 255, 0.1);
      color: var(--text-subtle);
      cursor: not-allowed;
      box-shadow: none;
      transform: none;
    }

    .dock-caption {
      text-align: center;
      font-size: 0.72rem;
      color: var(--text-subtle);
      margin-top: 8px;
    }
  </style>
</head>
<body>

  <!-- Left Sidebar -->
  <aside>
    <div class="sidebar-top">
      <div class="brand-block">
        <div class="brand-icon">🌿</div>
        <div>
          <div class="brand-title">Darukaa.Earth</div>
          <div class="brand-sub">AI Biodiversity Intelligence</div>
        </div>
      </div>
      <button class="btn-new-chat" onclick="handleNewConsultation()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        <span>New Consultation</span>
      </button>
    </div>

    <div class="sidebar-history-label">Consultation History</div>
    <div class="sidebar-chats" id="chat-history-list"></div>

    <div class="sidebar-footer">
      <div class="system-status">
        <div class="status-indicator"></div>
        <span>NVIDIA Nemotron 550B</span>
      </div>
      <div>OpenRouter Gateway &bull; 5 Domains</div>
      <div>Multi-Metric Grounded Reasoning</div>
    </div>
  </aside>

  <!-- Main Canvas -->
  <div class="main-workspace">
    <div class="top-header">
      <div class="header-context">
        <span style="font-size: 18px;">🌱</span>
        <span>Active Consultation:</span>
        <span class="header-pill" id="session-badge">session_init</span>
      </div>
      <div class="header-links">
        <a href="/docs" target="_blank" class="btn-header">API Docs</a>
        <button class="btn-header" onclick="handleClearSession()">Clear Thread</button>
      </div>
    </div>

    <!-- Scrollable Flow -->
    <div class="chat-scroll-area" id="scroll-area">
      <div class="chat-flow" id="chat-flow">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Input Dock -->
    <div class="input-dock">
      <div class="input-form">
        <textarea 
          id="query-input" 
          class="main-input" 
          rows="1" 
          placeholder="Describe land conditions, ask questions, or follow up..."
          oninput="adjustInputHeight(this)"
          onkeydown="processKey(event)"
        ></textarea>
        <button id="submit-btn" class="btn-send" onclick="submitMessage()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
      <div class="dock-caption">
        Darukaa AI uses NVIDIA Nemotron on OpenRouter + deterministic ecological reasoning. All evidence is grounded in peer-reviewed science.
      </div>
    </div>
  </div>

  <script>
    let activeSessionId = 'session_' + Math.random().toString(36).substring(2, 8);
    let sessionStore = JSON.parse(localStorage.getItem('darukaa_sessions_v3') || '{}');
    let isRequestActive = false;

    function init() {
      document.getElementById('session-badge').textContent = activeSessionId;
      renderHistoryList();
      renderChatScreen();
    }

    function adjustInputHeight(el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 140) + 'px';
    }

    function processKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitMessage();
      }
    }

    function handleNewConsultation() {
      if (isRequestActive) return;
      activeSessionId = 'session_' + Math.random().toString(36).substring(2, 8);
      document.getElementById('session-badge').textContent = activeSessionId;
      renderChatScreen();
      renderHistoryList();
    }

    function handleClearSession() {
      if (isRequestActive) return;
      delete sessionStore[activeSessionId];
      saveSessions();
      handleNewConsultation();
    }

    function saveSessions() {
      localStorage.setItem('darukaa_sessions_v3', JSON.stringify(sessionStore));
    }

    function renderHistoryList() {
      const container = document.getElementById('chat-history-list');
      container.innerHTML = '';
      const ids = Object.keys(sessionStore).reverse();

      ids.forEach(id => {
        const item = document.createElement('div');
        item.className = 'history-item ' + (id === activeSessionId ? 'active' : '');
        item.onclick = () => switchToSession(id);
        item.innerHTML = `
          <span class="history-item-title">💬 ${escapeStr(sessionStore[id].title || 'Consultation')}</span>
          <span class="history-delete-btn" onclick="event.stopPropagation(); deleteHistorySession('${id}')">✕</span>
        `;
        container.appendChild(item);
      });
    }

    function switchToSession(id) {
      if (isRequestActive) return;
      activeSessionId = id;
      document.getElementById('session-badge').textContent = activeSessionId;
      renderChatScreen();
      renderHistoryList();
    }

    function deleteHistorySession(id) {
      delete sessionStore[id];
      saveSessions();
      if (id === activeSessionId) {
        handleNewConsultation();
      } else {
        renderHistoryList();
      }
    }

    function renderChatScreen() {
      const flow = document.getElementById('chat-flow');
      flow.innerHTML = '';

      const messages = sessionStore[activeSessionId]?.messages || [];

      if (messages.length === 0) {
        flow.innerHTML = `
          <div class="hero-container">
            <div class="hero-badge">AI Environmental Scientist</div>
            <h1 class="hero-title">Biodiversity Intelligence Platform</h1>
            <p class="hero-description">
              Multi-variable reasoning across soil carbon, aridity, land use, and species metrics. Grounded in peer-reviewed ecological research.
            </p>
            <div class="prompt-grid">
              <div class="prompt-card" onclick="sendPrompt('My soil organic carbon is 0.3%, annual rainfall is low, and the land use is monoculture.')">
                <div class="prompt-card-header">
                  <span class="prompt-card-icon">🌾</span>
                  <span class="prompt-card-title">Low Carbon & Semi-Arid Monoculture</span>
                </div>
                <div class="prompt-card-desc">Soil carbon 0.3%, low rainfall, monoculture wheat (Challenge Benchmark)</div>
              </div>
              <div class="prompt-card" onclick="sendPrompt('Biodiversity is declining on my land.')">
                <div class="prompt-card-header">
                  <span class="prompt-card-icon">❓</span>
                  <span class="prompt-card-title">Incomplete Land Query</span>
                </div>
                <div class="prompt-card-desc">Tests multi-turn diagnostic questions and clarification memory</div>
              </div>
              <div class="prompt-card" onclick="sendPrompt('My soil pH is 5.2, organic carbon is 0.4%, and earthworm count is rare.')">
                <div class="prompt-card-header">
                  <span class="prompt-card-icon">🧪</span>
                  <span class="prompt-card-title">Acidic Soil & Declining Biology</span>
                </div>
                <div class="prompt-card-desc">Evaluates pH-nutrient availability and biological indicator metrics</div>
              </div>
              <div class="prompt-card" onclick="sendPrompt('What are the peer-reviewed benefits of agroforestry in drylands?')">
                <div class="prompt-card-header">
                  <span class="prompt-card-icon">🌳</span>
                  <span class="prompt-card-title">Dryland Agroforestry Research</span>
                </div>
                <div class="prompt-card-desc">Inspect FAO/IPBES citable evidence and canopy shade dynamics</div>
              </div>
            </div>
          </div>
        `;
        return;
      }

      messages.forEach(msg => {
        if (msg.role === 'user') {
          renderUserRow(msg.text);
        } else {
          renderAiRow(msg.data);
        }
      });
      scrollToBottom();
    }

    function sendPrompt(text) {
      if (isRequestActive) return;
      const input = document.getElementById('query-input');
      input.value = text;
      submitMessage();
    }

    async function submitMessage() {
      if (isRequestActive) return;
      const input = document.getElementById('query-input');
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      input.style.height = 'auto';

      if (!sessionStore[activeSessionId]) {
        sessionStore[activeSessionId] = {
          title: text.length > 32 ? text.substring(0, 30) + '...' : text,
          messages: []
        };
      }

      if (sessionStore[activeSessionId].messages.length === 0) {
        document.getElementById('chat-flow').innerHTML = '';
      }

      sessionStore[activeSessionId].messages.push({ role: 'user', text: text });
      saveSessions();
      renderUserRow(text);
      renderHistoryList();

      lastSubmittedPrompt = text;
      renderThinkingIndicator();
      scrollToBottom();

      isRequestActive = true;
      document.getElementById('submit-btn').disabled = true;

      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: activeSessionId, message: text })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => null);
          let msg = 'API request returned HTTP ' + response.status;
          if (response.status === 429) {
            msg = 'OpenRouter API Rate Limit Reached (HTTP 429: Too Many Requests). The active model has exceeded its request quota. Please wait a few moments before trying again.';
          } else if (response.status === 402) {
            msg = 'OpenRouter API Payment Required (HTTP 402). Insufficient usage credits for this model. Switch to the free tier model (nvidia/nemotron-3-ultra-550b-a55b:free) or add credits.';
          } else if (errData && (errData.message || errData.detail)) {
            msg = errData.message || errData.detail;
          }
          throw new Error(msg);
        }

        const data = await response.json();
        removeThinkingIndicator();

        sessionStore[activeSessionId].messages.push({ role: 'ai', data: data });
        saveSessions();
        renderAiRow(data);
      } catch (err) {
        removeThinkingIndicator();
        renderErrorRow(err.message);
      } finally {
        isRequestActive = false;
        document.getElementById('submit-btn').disabled = false;
        scrollToBottom();
      }
    }

    let lastSubmittedPrompt = '';

    function createErrorCardHtml(msg, statusCode) {
      const text = String(msg || '');
      const code = statusCode || (text.includes('429') ? 429 : text.includes('402') ? 402 : text.includes('401') ? 401 : null);
      let title = 'OpenRouter API Error';
      let badge = code ? `HTTP ${code}` : 'API Notice';

      if (code === 429) {
        title = 'API Rate Limit Reached';
        badge = 'HTTP 429 • Rate Limit';
      } else if (code === 402) {
        title = 'API Usage Credits Required';
        badge = 'HTTP 402 • Payment Required';
      } else if (code === 401) {
        title = 'API Unauthorized';
        badge = 'HTTP 401 • Invalid Key';
      }

      return `
        <div class="api-error-card">
          <div class="api-error-header">
            <div class="api-error-title-wrap">
              <div class="api-error-icon-box">⚠️</div>
              <div class="api-error-title">${escapeStr(title)}</div>
            </div>
            <span class="api-error-badge">${escapeStr(badge)}</span>
          </div>
          <div class="api-error-message">${escapeStr(text)}</div>
        </div>
      `;
    }

    function renderUserRow(text) {
      const flow = document.getElementById('chat-flow');
      const row = document.createElement('div');
      row.className = 'chat-row user';
      row.innerHTML = `<div class="chat-bubble">${escapeStr(text)}</div>`;
      flow.appendChild(row);
    }

    function renderThinkingIndicator() {
      const flow = document.getElementById('chat-flow');
      const row = document.createElement('div');
      row.className = 'thinking-row';
      row.id = 'active-thinking-row';
      row.innerHTML = `
        <div class="chat-avatar ai">🌿</div>
        <div class="thinking-bubble">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
          <span class="thinking-label">Reasoning across ecological metrics with Nemotron...</span>
        </div>
      `;
      flow.appendChild(row);
    }

    function removeThinkingIndicator() {
      const row = document.getElementById('active-thinking-row');
      if (row) row.remove();
    }

    function renderErrorRow(errorMsg) {
      const flow = document.getElementById('chat-flow');
      const row = document.createElement('div');
      row.className = 'chat-row ai';
      row.innerHTML = `
        <div class="chat-avatar ai" style="border-color: rgba(239, 68, 68, 0.5); color: #f87171;">⚠️</div>
        <div class="chat-bubble" style="background: transparent; border: none; padding: 0; box-shadow: none; width: 100%; max-width: 90%;">
          ${createErrorCardHtml(errorMsg)}
        </div>
      `;
      flow.appendChild(row);
    }

    function renderAiRow(data) {
      const flow = document.getElementById('chat-flow');

      if (data.type === 'error' || data.action === 'error') {
        const row = document.createElement('div');
        row.className = 'chat-row ai';
        row.innerHTML = `
          <div class="chat-avatar ai" style="border-color: rgba(239, 68, 68, 0.5); color: #f87171;">⚠️</div>
          <div class="chat-bubble" style="background: transparent; border: none; padding: 0; box-shadow: none; width: 100%; max-width: 90%;">
            ${createErrorCardHtml(data.message || data.narrated, data.status_code)}
          </div>
        `;
        flow.appendChild(row);
        return;
      }

      const row = document.createElement('div');
      row.className = 'chat-row ai';

      let inner = '';
      if (data.type === 'clarification') {
        inner = `
          <div class="clarification-callout">
            <div class="head">
              <span>❓</span>
              <span>Missing Ecological Variables (Diagnostic Question)</span>
            </div>
            <div class="content">${escapeStr(data.message)}</div>
          </div>
        `;
      } else if (data.type === 'recommendation') {
        const metricsHtml = (data.impacted_metrics || [])
          .map(m => `<span class="code-pill">📈 ${escapeStr(m)}</span>`)
          .join('');

        const interactionsHtml = (data.interactions_applied || [])
          .map(i => `<span class="code-pill" style="color: #fde68a;">⚡ ${escapeStr(i)}</span>`)
          .join('');

        const evidenceHtml = (data.evidence || [])
          .map(e => `
            <div class="citation-entry">
              <span class="citation-source">📄 ${escapeStr(e.source)}</span>
              <span class="citation-badge">${escapeStr(e.evidence_type || 'evidence')}</span>
            </div>
          `)
          .join('');

        inner = `
          <div class="intervention-header">
            <div class="intervention-title">🎯 ${escapeStr(data.what)}</div>
            <div class="tag-group">
              ${data.confidence ? `<span class="pill-tag pill-confidence">${escapeStr(data.confidence)} conf</span>` : ''}
              ${data.time_horizon ? `<span class="pill-tag pill-horizon">${escapeStr(data.time_horizon)} term</span>` : ''}
            </div>
          </div>

          <div class="meta-section-heading">Scientific Grounding & Rationale (Nemotron)</div>
          <div class="narrative-body">${escapeStr(data.why)}</div>

          ${interactionsHtml ? `
            <div class="meta-section-heading">Applied Multi-Metric Interactions</div>
            <div class="meta-pills-row">${interactionsHtml}</div>
          ` : ''}

          <div class="meta-section-heading">Impacted Environmental Metrics</div>
          <div class="meta-pills-row">${metricsHtml}</div>

          <div class="meta-section-heading">Peer-Reviewed Citations</div>
          <div class="citations-card">${evidenceHtml}</div>

          ${data.limitations ? `
            <div class="limitations-box">
              ⚠️ <strong>Boundary condition:</strong> ${escapeStr(data.limitations)}
            </div>
          ` : ''}

          <div class="followups-block">
            <div class="meta-section-heading">Recommended Follow-ups:</div>
            <button class="followup-btn" onclick="sendPrompt('How do I manage this intervention during severe dry spells?')">
              💧 How do I manage this intervention during severe dry spells?
            </button>
            <button class="followup-btn" onclick="sendPrompt('What if annual rainfall drops further below 250mm?')">
              📉 What if annual rainfall drops further below 250mm?
            </button>
            <button class="followup-btn" onclick="sendPrompt('Can this improve soil microbial biomass carbon within the first season?')">
              🔬 Can this improve soil microbial biomass carbon within the first season?
            </button>
          </div>
        `;
      } else {
        inner = `<div>${escapeStr(data.message || JSON.stringify(data))}</div>`;
      }

      row.innerHTML = `
        <div class="chat-avatar ai">🌿</div>
        <div class="chat-bubble">${inner}</div>
      `;
      flow.appendChild(row);
    }

    function scrollToBottom() {
      const area = document.getElementById('scroll-area');
      area.scrollTo({ top: area.scrollHeight, behavior: 'smooth' });
    }

    function escapeStr(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    window.onload = init;
  </script>
</body>
</html>
"""
