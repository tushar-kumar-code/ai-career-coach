/**
 * AI Career Coach - 100% Pure Vanilla JavaScript Engine
 * Author: tushar-kumar-code
 * Architecture: Vanilla JS (ES6+) connecting to Python FastAPI Backend
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Starter Prompts Data
const STARTER_PROMPTS = [
  {
    category: 'resume',
    label: 'ATS Optimization',
    text: 'How do I optimize my resume bullet points using the Google XYZ formula for tech jobs?'
  },
  {
    category: 'resume',
    label: 'Skill Gap Analysis',
    text: 'What are the most in-demand technologies to highlight on my profile for a Software Developer role?'
  },
  {
    category: 'coding',
    label: 'Core Data Structures',
    text: 'What are the top patterns (e.g. Two Pointers, Sliding Window, DP) asked in Coding rounds?'
  },
  {
    category: 'coding',
    label: 'Time & Space Complexity',
    text: 'How can I quickly analyze and explain Big-O Time & Space Complexity during a live technical interview?'
  },
  {
    category: 'design',
    label: 'Caching & Scaling',
    text: 'Can you explain the key concepts of System Design: Redis Caching, Sharding, and Load Balancing simply?'
  },
  {
    category: 'design',
    label: 'SQL vs NoSQL',
    text: 'When should I choose SQL vs NoSQL in system architecture interviews?'
  },
  {
    category: 'interview',
    label: 'STAR Framework',
    text: 'What is the best way to structure behavioral answers using the STAR (Situation, Task, Action, Result) method?'
  },
  {
    category: 'interview',
    label: 'Conflict Resolution',
    text: 'How do I answer: "Tell me about a time you disagreed with an engineering decision or teammate"?'
  }
];

// App State
const state = {
  activeTab: 'chat',
  isWideMode: false,
  isLargeFont: false,
  isHeaderVisible: true,
  showTopics: true,
  activeCategory: 'all',
  messages: [
    {
      id: 'welcome-1',
      sender: 'ai',
      text: `### 👋 Welcome to your **Contextual AI Career Coach**!
I am synchronized with your **target career**, **ATS Resume scanner**, and **personalized learning roadmap**.

### 🎯 How I Can Accelerate Your Career:
- **Technical Mastery**: Deep dive into Coding, DSA, System Design, and Backend/Frontend architectures.
- **Resume & ATS Strategy**: Tailor your accomplishments into high-impact bullet points.
- **Mock Interview Drills**: Master behavioral (STAR method) and technical interview challenges.

*Feel free to ask any question below in English or Hinglish!*`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ],
  apiKey: localStorage.getItem('ai_coach_key') || '',
  provider: localStorage.getItem('ai_coach_provider') || 'groq',
  speakingId: null
};

// DOM Elements
const elements = {
  appContainer: document.querySelector('.app-container'),
  tabs: document.querySelectorAll('.nav-tab'),
  tabPanes: document.querySelectorAll('.tab-pane'),
  messagesContainer: document.getElementById('messagesContainer'),
  chatInput: document.getElementById('chatInput'),
  sendBtn: document.getElementById('sendBtn'),
  clearChatBtn: document.getElementById('clearChatBtn'),
  fontSizeBtn: document.getElementById('fontSizeBtn'),
  fontText: document.getElementById('fontText'),
  wideModeBtn: document.getElementById('wideModeBtn'),
  wideText: document.getElementById('wideText'),
  hideHeaderBtn: document.getElementById('hideHeaderBtn'),
  showHeaderBtn: document.getElementById('showHeaderBtn'),
  chatHeader: document.getElementById('chatHeader'),
  chatMicroBar: document.getElementById('chatMicroBar'),
  microFontBtn: document.getElementById('microFontBtn'),
  microWideBtn: document.getElementById('microWideBtn'),
  microClearBtn: document.getElementById('microClearBtn'),
  starterTopicsContainer: document.getElementById('starterTopicsContainer'),
  hideTopicsBtn: document.getElementById('hideTopicsBtn'),
  unhideTopicsBar: document.getElementById('unhideTopicsBar'),
  showTopicsBtn: document.getElementById('showTopicsBtn'),
  promptCardsGrid: document.getElementById('promptCardsGrid'),
  categoryPills: document.querySelectorAll('.pill'),
  backendStatus: document.getElementById('backendStatus'),
  apiKeyBtn: document.getElementById('apiKeyBtn'),
  keyBtnText: document.getElementById('keyBtnText'),
  apiKeyModal: document.getElementById('apiKeyModal'),
  closeModalBtn: document.getElementById('closeModalBtn'),
  cancelModalBtn: document.getElementById('cancelModalBtn'),
  saveKeyBtn: document.getElementById('saveKeyBtn'),
  modalProviderSelect: document.getElementById('modalProviderSelect'),
  modalKeyInput: document.getElementById('modalKeyInput'),
  // Resume Elements
  analyzeResumeBtn: document.getElementById('analyzeResumeBtn'),
  resumeTextInput: document.getElementById('resumeTextInput'),
  targetRoleInput: document.getElementById('targetRoleInput'),
  atsScoreValue: document.getElementById('atsScoreValue'),
  atsStatusHeading: document.getElementById('atsStatusHeading'),
  atsSummaryText: document.getElementById('atsSummaryText'),
  // Interview Elements
  submitAnswerBtn: document.getElementById('submitAnswerBtn'),
  interviewAnswerInput: document.getElementById('interviewAnswerInput'),
  feedbackContainer: document.getElementById('feedbackContainer'),
  nextQuestionBtn: document.getElementById('nextQuestionBtn'),
  // Assessment Elements
  careerChipsGrid: document.getElementById('careerChipsGrid'),
  customRoleToggle: document.getElementById('customRoleToggle'),
  customRoleInput: document.getElementById('customRoleInput'),
  lvlScratch: document.getElementById('lvlScratch'),
  lvlBeginner: document.getElementById('lvlBeginner'),
  lvlIntermediate: document.getElementById('lvlIntermediate'),
  scratchBanner: document.getElementById('scratchBanner'),
  skillsPickerArea: document.getElementById('skillsPickerArea'),
  skillsTagsGrid: document.getElementById('skillsTagsGrid'),
  customSkillInput: document.getElementById('customSkillInput'),
  addCustomSkillBtn: document.getElementById('addCustomSkillBtn'),
  submitGoalBtn: document.getElementById('submitGoalBtn'),
  goalResultCard: document.getElementById('goalResultCard')
};

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initAssessmentAndGoals();
  initChat();
  initStarterPrompts();
  initApiKeyModal();
  initResumeScanner();
  initInterviewMock();
  checkBackendHealth();
  updateKeyButtonUI();
});

// ================= TAB NAVIGATION =================
function initTabs() {
  elements.tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const tabTarget = tab.getAttribute('data-tab');
      elements.tabs.forEach((t) => t.classList.remove('active'));
      elements.tabPanes.forEach((p) => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPane = document.getElementById(`tab-${tabTarget}`);
      if (targetPane) targetPane.classList.add('active');
      state.activeTab = tabTarget;
    });
  });
}

// ================= CHAT FUNCTIONS =================
function initChat() {
  renderMessages();

  // Send message events
  elements.sendBtn.addEventListener('click', () => handleSendMessage());
  elements.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  // Auto-expanding textarea
  elements.chatInput.addEventListener('input', () => {
    elements.chatInput.style.height = 'auto';
    elements.chatInput.style.height = `${Math.min(elements.chatInput.scrollHeight, 130)}px`;
  });

  // Clear chat
  elements.clearChatBtn.addEventListener('click', handleClearChat);
  elements.microClearBtn.addEventListener('click', handleClearChat);

  // Font size toggle
  elements.fontSizeBtn.addEventListener('click', toggleFontSize);
  elements.microFontBtn.addEventListener('click', toggleFontSize);

  // Wide mode toggle
  elements.wideModeBtn.addEventListener('click', toggleWideMode);
  elements.microWideBtn.addEventListener('click', toggleWideMode);

  // Header Hide/Unhide
  elements.hideHeaderBtn.addEventListener('click', () => setHeaderVisibility(false));
  elements.showHeaderBtn.addEventListener('click', () => setHeaderVisibility(true));

  // Topics Hide/Unhide
  elements.hideTopicsBtn.addEventListener('click', () => setTopicsVisibility(false));
  elements.showTopicsBtn.addEventListener('click', () => setTopicsVisibility(true));
}

function setHeaderVisibility(visible) {
  state.isHeaderVisible = visible;
  if (visible) {
    elements.chatHeader.style.display = 'flex';
    elements.chatMicroBar.style.display = 'none';
  } else {
    elements.chatHeader.style.display = 'none';
    elements.chatMicroBar.style.display = 'flex';
  }
}

function setTopicsVisibility(visible) {
  state.showTopics = visible;
  if (visible) {
    elements.starterTopicsContainer.style.display = 'flex';
    elements.unhideTopicsBar.style.display = 'none';
  } else {
    elements.starterTopicsContainer.style.display = 'none';
    elements.unhideTopicsBar.style.display = 'block';
  }
}

function toggleFontSize() {
  state.isLargeFont = !state.isLargeFont;
  if (state.isLargeFont) {
    elements.appContainer.classList.add('font-large');
    elements.fontText.textContent = 'Text A';
  } else {
    elements.appContainer.classList.remove('font-large');
    elements.fontText.textContent = 'Text A+';
  }
}

function toggleWideMode() {
  state.isWideMode = !state.isWideMode;
  if (state.isWideMode) {
    elements.appContainer.classList.add('wide-mode');
    elements.wideText.textContent = 'Standard';
  } else {
    elements.appContainer.classList.remove('wide-mode');
    elements.wideText.textContent = 'Wide Mode';
  }
}

function handleClearChat() {
  state.messages = [
    {
      id: `welcome-${Date.now()}`,
      sender: 'ai',
      text: '### 🚀 New Coaching Session Started\n\nWhat career topic, technical concept, or interview scenario would you like to explore today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ];
  renderMessages();
}

async function handleSendMessage(customText) {
  const text = (customText || elements.chatInput.value).trim();
  if (!text) return;

  // Add User message
  const userMsg = {
    id: `user-${Date.now()}`,
    sender: 'user',
    text: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  };

  state.messages.push(userMsg);
  elements.chatInput.value = '';
  elements.chatInput.style.height = 'auto';
  renderMessages();

  // Show typing indicator
  const typingMsg = {
    id: 'typing',
    sender: 'ai',
    text: '⏳ *AI Coach is structuring your personalized career answer...*',
    timestamp: ''
  };
  state.messages.push(typingMsg);
  renderMessages();

  try {
    const historyPayload = state.messages
      .filter((m) => m.id !== 'typing')
      .slice(-8)
      .map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

    // Call Python FastAPI Backend
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(state.apiKey ? { 'X-AI-API-Key': state.apiKey, 'X-AI-Provider': state.provider } : {})
      },
      body: JSON.stringify({
        message: text,
        history: historyPayload
      })
    });

    const data = await response.json();
    state.messages = state.messages.filter((m) => m.id !== 'typing');

    if (data.success && data.data && data.data.response) {
      state.messages.push({
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: data.data.response,
        timestamp: data.data.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
    } else {
      // Local intelligent response fallback
      state.messages.push({
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: generateFallbackReply(text),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
    }
  } catch (err) {
    console.error('Chat error:', err);
    state.messages = state.messages.filter((m) => m.id !== 'typing');
    state.messages.push({
      id: `ai-${Date.now()}`,
      sender: 'ai',
      text: generateFallbackReply(text),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
  }

  renderMessages();
}

// Simple and robust markdown converter for Vanilla JS
function formatMarkdown(text) {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Fenced Code blocks
  html = html.replace(/```([\w]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code>${code.trim()}</code></pre>`;
  });

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // Bold & Italic & Inline Code
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Horizontal rules
  html = html.replace(/^---$/gim, '<hr/>');

  // Bullet Lists
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Line breaks
  html = html.replace(/\n\n/g, '<br/><br/>');

  return html;
}

function renderMessages() {
  elements.messagesContainer.innerHTML = '';

  state.messages.forEach((msg) => {
    const row = document.createElement('div');
    row.className = `message-row ${msg.sender === 'user' ? 'user-row' : 'ai-row'}`;

    if (msg.sender === 'ai') {
      const avatar = document.createElement('div');
      avatar.className = 'message-avatar ai';
      avatar.textContent = '🤖';
      row.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMarkdown(msg.text);

    // Meta bar
    if (msg.id !== 'typing') {
      const meta = document.createElement('div');
      meta.className = 'message-meta';
      meta.innerHTML = `
        <span>${msg.timestamp}</span>
        <div class="meta-actions">
          ${msg.sender === 'ai' ? `
            <button class="meta-btn" onclick="speakMessage('${msg.id}')" title="Listen to answer">🔊 Listen</button>
            <button class="meta-btn" onclick="copyMessageText('${msg.id}')" title="Copy text">📋 Copy</button>
          ` : ''}
        </div>
      `;
      bubble.appendChild(meta);
    }

    row.appendChild(bubble);

    if (msg.sender === 'user') {
      const avatar = document.createElement('div');
      avatar.className = 'message-avatar user';
      avatar.textContent = '👤';
      row.appendChild(avatar);
    }

    elements.messagesContainer.appendChild(row);
  });

  // Scroll to bottom
  elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

// Window functions for message actions
window.copyMessageText = function (msgId) {
  const msg = state.messages.find((m) => m.id === msgId);
  if (msg) {
    navigator.clipboard.writeText(msg.text);
    alert('Copied message to clipboard!');
  }
};

window.speakMessage = function (msgId) {
  if (!('speechSynthesis' in window)) {
    alert('Speech synthesis not supported in this browser.');
    return;
  }

  const msg = state.messages.find((m) => m.id === msgId);
  if (!msg) return;

  if (state.speakingId === msgId) {
    window.speechSynthesis.cancel();
    state.speakingId = null;
    return;
  }

  window.speechSynthesis.cancel();
  const clean = msg.text.replace(/[#*`_>-]/g, '');
  const utter = new SpeechSynthesisUtterance(clean);
  utter.rate = 1.0;
  utter.onend = () => (state.speakingId = null);
  utter.onerror = () => (state.speakingId = null);

  state.speakingId = msgId;
  window.speechSynthesis.speak(utter);
};

// ================= STARTER PROMPTS =================
function initStarterPrompts() {
  renderPromptCards('all');

  elements.categoryPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      elements.categoryPills.forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      const cat = pill.getAttribute('data-cat');
      renderPromptCards(cat);
    });
  });
}

function renderPromptCards(category) {
  elements.promptCardsGrid.innerHTML = '';
  const filtered = category === 'all'
    ? STARTER_PROMPTS
    : STARTER_PROMPTS.filter((p) => p.category === category);

  filtered.slice(0, 4).forEach((item) => {
    const card = document.createElement('button');
    card.className = 'prompt-card';
    card.innerHTML = `
      <span>✨</span>
      <div>
        <span class="prompt-card-title">${item.label}</span>
        <span class="prompt-card-desc">${item.text}</span>
      </div>
    `;
    card.addEventListener('click', () => {
      handleSendMessage(item.text);
    });
    elements.promptCardsGrid.appendChild(card);
  });
}

// Fallback Reply Engine if backend offline
function generateFallbackReply(userText) {
  const lower = userText.toLowerCase();

  if (lower.includes('data analyst') || lower.includes('non-tech')) {
    return `### 🎯 Non-Tech se Data Analyst Banne Ka 3-Month Roadmap

Non-tech background se Data Analyst banna bilkul sambhav hai! Bas in 4 skills par focus karein:

### 📌 Step-by-Step Action Plan:
1. **Excel & Google Sheets (Week 1-2)**: VLOOKUP, XLOOKUP, Pivot Tables, aur Data Cleaning.
2. **SQL (Week 3-6)**: SELECT, JOINs, GROUP BY, Window Functions, aur subqueries.
3. **BI Dashboard Tool (Week 7-9)**: Power BI ya Tableau me 2 interactive dashboards banayein.
4. **Python Basics (Week 10-12)**: Pandas aur Matplotlib libraries data analysis ke liye.

### 💡 Pro Tip:
> Kaggle ya GitHub par 2 real-world analysis projects upload karein aur resume me live link add karein!`;
  }

  if (lower.includes('sql') || lower.includes('database')) {
    return `### ⚡ SQL vs NoSQL Quick Comparison

| Feature | SQL (Relational) | NoSQL (Non-Relational) |
|---|---|---|
| Schema | Fixed & Structured | Flexible / JSON Documents |
| Scaling | Vertical Scaling | Horizontal Scaling (Sharding) |
| Ideal For | Transactions (Banking, E-commerce) | Big Data, Real-time Feeds (Social, Logs) |
| Examples | PostgreSQL, MySQL | MongoDB, Redis, Cassandra |

### 💡 Interview Rule of Thumb:
> Agar ACID transactions aur strong relations zaroori hain toh SQL chunein; agar high-velocity unstructured data aur scaling chahiye toh NoSQL.`;
  }

  return `### 🎯 Career Guidance & Next Steps
Aapka sawal bahut relevant hai!

### 📌 Key Recommendations:
1. **Focus on Fundamentals**: Tech concepts ko practical project me apply karke seekhein.
2. **Project Portfolio**: Apne GitHub par 2-3 production-grade projects banayein jisme clean README aur demo link ho.
3. **Interview Practice**: STAR method use karke behavioral aur technical scenarios prepare karein.

Aap specific language ya role ke baare me aur detail me pooch sakte hain!`;
}

// ================= API KEY MODAL =================
function initApiKeyModal() {
  elements.apiKeyBtn.addEventListener('click', () => {
    elements.modalKeyInput.value = state.apiKey;
    elements.modalProviderSelect.value = state.provider;
    elements.apiKeyModal.style.display = 'flex';
  });

  elements.closeModalBtn.addEventListener('click', closeModal);
  elements.cancelModalBtn.addEventListener('click', closeModal);

  elements.saveKeyBtn.addEventListener('click', () => {
    const key = elements.modalKeyInput.value.trim();
    const prov = elements.modalProviderSelect.value;
    state.apiKey = key;
    state.provider = prov;
    localStorage.setItem('ai_coach_key', key);
    localStorage.setItem('ai_coach_provider', prov);
    updateKeyButtonUI();
    closeModal();
    alert('AI Key successfully saved locally!');
  });
}

function closeModal() {
  elements.apiKeyModal.style.display = 'none';
}

function updateKeyButtonUI() {
  if (state.apiKey) {
    elements.keyBtnText.textContent = `${state.provider.toUpperCase()} Active`;
  } else {
    elements.keyBtnText.textContent = 'Set AI Key';
  }
}

// ================= RESUME SCANNER =================
function initResumeScanner() {
  elements.analyzeResumeBtn.addEventListener('click', () => {
    const text = elements.resumeTextInput.value.trim();
    if (!text) {
      alert('Please paste some resume text first!');
      return;
    }

    elements.analyzeResumeBtn.textContent = 'Analyzing...';
    setTimeout(() => {
      // Compute deterministic score based on key tech terms
      const techKeywords = ['python', 'react', 'sql', 'fastapi', 'javascript', 'git', 'docker', 'api', 'database'];
      const matches = techKeywords.filter((kw) => text.toLowerCase().includes(kw));
      const score = Math.min(60 + matches.length * 5, 95);

      elements.atsScoreValue.textContent = `${score}%`;
      elements.atsStatusHeading.textContent = score >= 80 ? 'Strong Candidate Match' : 'Moderate Candidate Match';
      elements.atsSummaryText.textContent = `Found ${matches.length} key technical skills: ${matches.join(', ')}.`;
      elements.analyzeResumeBtn.textContent = '⚡ Run ATS Analysis';
    }, 600);
  });
}

// ================= MOCK INTERVIEW =================
const QUESTIONS = [
  "Can you explain the difference between SQL and NoSQL databases, and when would you choose one over the other?",
  "What is the difference between synchronous and asynchronous programming in Python or JavaScript?",
  "Describe a challenging bug you faced in a project and how you diagnosed and resolved it using the STAR method."
];
let currentQIdx = 0;

function initInterviewMock() {
  const qEl = document.getElementById('interviewQuestion');

  elements.nextQuestionBtn.addEventListener('click', () => {
    currentQIdx = (currentQIdx + 1) % QUESTIONS.length;
    qEl.textContent = `"${QUESTIONS[currentQIdx]}"`;
    elements.interviewAnswerInput.value = '';
    elements.feedbackContainer.style.display = 'none';
  });

  elements.submitAnswerBtn.addEventListener('click', () => {
    const ans = elements.interviewAnswerInput.value.trim();
    if (!ans) {
      alert('Please type an answer to get AI evaluation!');
      return;
    }

    elements.submitAnswerBtn.textContent = 'Evaluating with AI...';
    setTimeout(() => {
      elements.submitAnswerBtn.textContent = 'Submit Answer for AI Evaluation';
      elements.feedbackContainer.style.display = 'block';
    }, 700);
  });
}

// ================= BACKEND HEALTH CHECK =================
async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    const data = await res.json();
    if (data.status === 'healthy') {
      elements.backendStatus.innerHTML = '<span class="status-dot"></span> Backend: Python Online';
    }
  } catch (e) {
    elements.backendStatus.innerHTML = '<span class="status-dot" style="background:#f59e0b"></span> Backend: Offline (Local Mode)';
  }
}

// ================= ASSESSMENT & CAREER GOAL LOGIC =================
const CAREER_PRESETS = [
  {
    title: 'Frontend Developer',
    icon: '💻',
    category: 'Web & UI',
    skills: ['HTML', 'CSS', 'JavaScript', 'React', 'TypeScript', 'Tailwind CSS', 'Git', 'Next.js']
  },
  {
    title: 'Backend Developer',
    icon: '⚙️',
    category: 'Engineering',
    skills: ['Python', 'Node.js', 'FastAPI', 'PostgreSQL', 'REST APIs', 'Docker', 'Git', 'SQL']
  },
  {
    title: 'Fullstack Developer',
    icon: '🌐',
    category: 'Full-Stack',
    skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'SQL', 'Git', 'REST APIs', 'MongoDB']
  },
  {
    title: 'Data Analyst',
    icon: '📊',
    category: 'Data & Analytics',
    skills: ['Python', 'SQL', 'Excel', 'PowerBI', 'Tableau', 'Pandas', 'Statistics']
  },
  {
    title: 'Machine Learning / AI Engineer',
    icon: '🤖',
    category: 'AI & Data',
    skills: ['Python', 'NumPy', 'Pandas', 'Machine Learning', 'Deep Learning', 'PyTorch', 'LLMs']
  },
  {
    title: 'Cloud & DevOps Engineer',
    icon: '☁️',
    category: 'Infrastructure',
    skills: ['Linux', 'Git', 'Docker', 'Kubernetes', 'AWS', 'CI/CD Pipelines', 'Terraform']
  },
  {
    title: 'Cyber Security Analyst',
    icon: '🛡️',
    category: 'Security',
    skills: ['Networking Fundamentals', 'Linux', 'Security Protocols', 'Wireshark', 'Ethical Hacking']
  },
  {
    title: 'Mobile App Developer',
    icon: '📱',
    category: 'Mobile Apps',
    skills: ['Flutter', 'React Native', 'Dart', 'JavaScript', 'Mobile UI/UX', 'REST APIs']
  },
  {
    title: 'UI/UX Designer',
    icon: '🎨',
    category: 'Design',
    skills: ['Figma', 'User Research', 'Wireframing', 'Prototyping', 'Design Systems']
  },
  {
    title: 'QA / Software Tester',
    icon: '🧪',
    category: 'Testing',
    skills: ['Manual Testing', 'Selenium', 'Python / Java', 'API Testing (Postman)', 'Jira']
  }
];

let selectedRole = 'Frontend Developer';
let selectedLevel = 'scratch';
let knownSkills = [];

function initAssessmentAndGoals() {
  if (!elements.careerChipsGrid) return;

  // Render role presets
  renderCareerChips();

  // Custom role toggle
  if (elements.customRoleToggle) {
    elements.customRoleToggle.addEventListener('change', (e) => {
      elements.customRoleInput.style.display = e.target.checked ? 'block' : 'none';
      if (e.target.checked) {
        document.querySelectorAll('.career-chip').forEach(c => c.classList.remove('active'));
      } else {
        const firstChip = document.querySelector('.career-chip');
        if (firstChip) firstChip.classList.add('active');
        selectedRole = CAREER_PRESETS[0].title;
        renderSkillTags();
      }
    });
  }

  // Level selector click handlers
  [elements.lvlScratch, elements.lvlBeginner, elements.lvlIntermediate].forEach((lvlCard) => {
    if (!lvlCard) return;
    lvlCard.addEventListener('click', () => {
      [elements.lvlScratch, elements.lvlBeginner, elements.lvlIntermediate].forEach(c => {
        c.classList.remove('active');
        c.style.borderColor = '#334155';
        c.style.background = 'rgba(15, 23, 42, 0.6)';
      });

      lvlCard.classList.add('active');
      const lvl = lvlCard.getAttribute('data-level');
      selectedLevel = lvl;

      if (lvl === 'scratch') {
        lvlCard.style.borderColor = '#10b981';
        lvlCard.style.background = 'rgba(16, 185, 129, 0.1)';
        elements.scratchBanner.style.display = 'flex';
        elements.skillsPickerArea.style.display = 'none';
        knownSkills = [];
      } else {
        lvlCard.style.borderColor = lvl === 'beginner' ? '#6366f1' : '#a855f7';
        lvlCard.style.background = lvl === 'beginner' ? 'rgba(99, 102, 241, 0.1)' : 'rgba(168, 85, 247, 0.1)';
        elements.scratchBanner.style.display = 'none';
        elements.skillsPickerArea.style.display = 'block';
        renderSkillTags();
      }
    });
  });

  // Custom skill adder
  if (elements.addCustomSkillBtn && elements.customSkillInput) {
    const addCustom = () => {
      const val = elements.customSkillInput.value.trim();
      if (val && !knownSkills.includes(val)) {
        knownSkills.push(val);
        elements.customSkillInput.value = '';
        renderSkillTags();
      }
    };
    elements.addCustomSkillBtn.addEventListener('click', addCustom);
    elements.customSkillInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addCustom();
      }
    });
  }

  // Submit Goal Handler
  if (elements.submitGoalBtn) {
    elements.submitGoalBtn.addEventListener('click', handleGoalSubmit);
  }
}

function renderCareerChips() {
  if (!elements.careerChipsGrid) return;
  elements.careerChipsGrid.innerHTML = '';

  CAREER_PRESETS.forEach((preset, idx) => {
    const chip = document.createElement('div');
    chip.className = `career-chip ${idx === 0 ? 'active' : ''}`;
    chip.innerHTML = `
      <span class="chip-icon">${preset.icon}</span>
      <span class="chip-title">${preset.title}</span>
      <span class="chip-category">${preset.category}</span>
    `;

    chip.addEventListener('click', () => {
      if (elements.customRoleToggle) elements.customRoleToggle.checked = false;
      if (elements.customRoleInput) elements.customRoleInput.style.display = 'none';

      document.querySelectorAll('.career-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedRole = preset.title;
      renderSkillTags();
    });

    elements.careerChipsGrid.appendChild(chip);
  });
}

function renderSkillTags() {
  if (!elements.skillsTagsGrid) return;
  elements.skillsTagsGrid.innerHTML = '';

  const currentPreset = CAREER_PRESETS.find(p => p.title === selectedRole) || {
    skills: ['Git', 'Problem Solving', 'Data Structures', 'REST APIs', 'SQL']
  };

  const allSkills = Array.from(new Set([...currentPreset.skills, ...knownSkills]));

  allSkills.forEach(skill => {
    const isSelected = knownSkills.includes(skill);
    const tag = document.createElement('span');
    tag.className = `skill-tag ${isSelected ? 'selected' : ''}`;
    tag.innerHTML = `<span>${isSelected ? '✓' : '＋'}</span> <span>${skill}</span>`;

    tag.addEventListener('click', () => {
      if (isSelected) {
        knownSkills = knownSkills.filter(s => s !== skill);
      } else {
        knownSkills.push(skill);
      }
      renderSkillTags();
    });

    elements.skillsTagsGrid.appendChild(tag);
  });
}

async function handleGoalSubmit() {
  const isCustom = elements.customRoleToggle && elements.customRoleToggle.checked;
  const targetCareer = isCustom ? elements.customRoleInput.value.trim() : selectedRole;

  if (!targetCareer) {
    alert('Please select or type your target career role!');
    return;
  }

  elements.submitGoalBtn.textContent = 'Analyzing Skill Gaps & Setting Goal...';
  elements.submitGoalBtn.disabled = true;

  const payload = {
    target_career: targetCareer,
    experience_level: selectedLevel,
    known_skills: selectedLevel === 'scratch' ? [] : knownSkills,
    custom_notes: selectedLevel === 'scratch' ? 'Starting completely from scratch (0 knowledge)' : `Selected ${knownSkills.length} known skills`
  };

  try {
    const res = await fetch(`${API_BASE_URL}/assessment/direct-goal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    let data;
    if (res.ok) {
      const json = await res.json();
      data = json.data || json;
    } else {
      throw new Error('API fallback');
    }

    renderGoalResult(data);
  } catch (err) {
    // Local intelligent fallback calculation
    const preset = CAREER_PRESETS.find(p => p.title === targetCareer);
    const catalogSkills = preset ? preset.skills : ['Git', 'Problem Solving', 'Data Structures', 'REST APIs', 'SQL'];
    const lowerKnown = knownSkills.map(s => s.toLowerCase());
    const verified = selectedLevel === 'scratch' ? [] : catalogSkills.filter(s => lowerKnown.includes(s.toLowerCase()));
    const missing = selectedLevel === 'scratch' ? catalogSkills : catalogSkills.filter(s => !lowerKnown.includes(s.toLowerCase()));
    const readiness = selectedLevel === 'scratch' ? 0 : Math.round((verified.length / catalogSkills.length) * 100);

    renderGoalResult({
      target_career: targetCareer,
      experience_level: selectedLevel,
      readiness_score: readiness,
      known_skills: verified,
      missing_gaps: missing
    });
  } finally {
    elements.submitGoalBtn.textContent = '🎯 Analyze My Skills & Save Career Goal';
    elements.submitGoalBtn.disabled = false;
  }
}

function renderGoalResult(data) {
  if (!elements.goalResultCard) return;

  // Persist target career
  localStorage.setItem('target_career', data.target_career);
  if (elements.targetRoleInput) elements.targetRoleInput.value = data.target_career;

  const isScratch = data.experience_level === 'scratch';

  elements.goalResultCard.style.display = 'block';
  elements.goalResultCard.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem; margin-bottom: 1rem;">
      <div>
        <span style="font-size: 0.75rem; font-weight: 700; color: #10b981; background: rgba(16, 185, 129, 0.2); padding: 0.2rem 0.6rem; border-radius: 99px;">
          🎯 Goal Set Successfully!
        </span>
        <h3 style="font-size: 1.3rem; font-weight: 800; color: #fff; margin-top: 0.4rem;">
          Target: <span style="color: #6ee7b7;">${data.target_career}</span>
        </h3>
        <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">
          Starting Level: <strong style="color: #fff; text-transform: capitalize;">${data.experience_level}</strong> 
          ${isScratch ? '(Day 1 Fundamentals to Mastery)' : ''}
        </p>
      </div>
      <div style="text-align: right; background: rgba(15, 23, 42, 0.7); padding: 0.5rem 1rem; border-radius: 12px; border: 1px solid #334155;">
        <span style="font-size: 0.7rem; color: #94a3b8;">Readiness</span>
        <div style="font-size: 1.5rem; font-weight: 900; color: #818cf8;">${data.readiness_score}%</div>
      </div>
    </div>

    <!-- Skill Gap Matrix -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;">
      <!-- Known Skills -->
      <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);">
        <h4 style="font-size: 0.8rem; font-weight: 700; color: #10b981; margin-bottom: 0.5rem;">
          ✓ Skills You Already Know (${data.known_skills ? data.known_skills.length : 0})
        </h4>
        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">
          ${data.known_skills && data.known_skills.length > 0
            ? data.known_skills.map(s => `<span style="font-size: 0.7rem; padding: 0.2rem 0.5rem; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; color: #6ee7b7;">${s}</span>`).join('')
            : '<span style="font-size: 0.75rem; color: #94a3b8;">Starting from scratch — no repeat required!</span>'
          }
        </div>
      </div>

      <!-- Missing Skills -->
      <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.2);">
        <h4 style="font-size: 0.8rem; font-weight: 700; color: #f59e0b; margin-bottom: 0.5rem;">
          ⚠️ Skills To Master in Roadmap (${data.missing_gaps ? data.missing_gaps.length : 0})
        </h4>
        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">
          ${data.missing_gaps && data.missing_gaps.length > 0
            ? data.missing_gaps.map(s => `<span style="font-size: 0.7rem; padding: 0.2rem 0.5rem; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; color: #fcd34d;">${s}</span>`).join('')
            : '<span style="font-size: 0.75rem; color: #6ee7b7;">All core skills mastered!</span>'
          }
        </div>
      </div>
    </div>

    <!-- Quick Transition Buttons -->
    <div style="display: flex; flex-wrap: wrap; gap: 0.75rem;">
      <button id="quickRoadmapBtn" class="btn btn-primary" style="flex: 1; padding: 0.75rem; font-size: 0.85rem;">
        🗺️ Open 3-Month Roadmap
      </button>
      <button id="quickChatBtn" class="btn btn-secondary" style="flex: 1; padding: 0.75rem; font-size: 0.85rem;">
        💬 Discuss with AI Coach
      </button>
      <button id="quickResumeBtn" class="btn btn-secondary" style="flex: 1; padding: 0.75rem; font-size: 0.85rem;">
        📄 Test ATS Resume
      </button>
    </div>
  `;

  // Update dynamic roadmap to reflect role
  updateDynamicRoadmap(data.target_career, data.experience_level, data.missing_gaps);

  // Wire up quick buttons
  document.getElementById('quickRoadmapBtn')?.addEventListener('click', () => switchTab('roadmap'));
  document.getElementById('quickChatBtn')?.addEventListener('click', () => {
    switchTab('chat');
    if (elements.chatInput) {
      elements.chatInput.value = `Mujhe ${data.target_career} banna hai aur main ${data.experience_level} se start kar raha hoon. Mujhe kya plan follow karna chahiye?`;
    }
  });
  document.getElementById('quickResumeBtn')?.addEventListener('click', () => switchTab('resume'));

  elements.goalResultCard.scrollIntoView({ behavior: 'smooth' });
}

function switchTab(tabId) {
  elements.tabs.forEach((t) => t.classList.remove('active'));
  elements.tabPanes.forEach((p) => p.classList.remove('active'));

  const tabBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  if (tabBtn) tabBtn.classList.add('active');

  const pane = document.getElementById(`tab-${tabId}`);
  if (pane) pane.classList.add('active');
  state.activeTab = tabId;
}

function updateDynamicRoadmap(role, level, gaps) {
  const isScratch = level === 'scratch';
  const timeline = document.querySelector('.roadmap-timeline');
  if (!timeline) return;

  const gapTags = (gaps && gaps.length > 0) ? gaps.slice(0, 4) : ['Core Fundamentals', 'Project Setup', 'Git', 'Syntax'];

  timeline.innerHTML = `
    <div class="roadmap-step">
      <div class="step-badge">Month 1</div>
      <div class="step-content">
        <h3>${isScratch ? 'Day 1 Basic Fundamentals & Tooling' : 'Core Architecture & Skill Reinforcement'}</h3>
        <p>${isScratch ? `Zero-to-Hero Foundation for ${role}: Basic syntax, dev environment, and problem solving basics.` : `Deep dive into ${role} prerequisites and strengthening foundation.`}</p>
        <div class="tags">
          ${gapTags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>
      </div>
    </div>

    <div class="roadmap-step">
      <div class="step-badge">Month 2</div>
      <div class="step-content">
        <h3>Production Projects & Practical Engineering</h3>
        <p>Build 2 industry-ready, portfolio projects demonstrating full capabilities in ${role}.</p>
        <div class="tags">
          <span class="tag">REST APIs</span>
          <span class="tag">State Management</span>
          <span class="tag">Database Integration</span>
          <span class="tag">Clean Code Standards</span>
        </div>
      </div>
    </div>

    <div class="roadmap-step">
      <div class="step-badge">Month 3</div>
      <div class="step-content">
        <h3>Placement Drills, ATS Resume & Mock Interviews</h3>
        <p>STAR behavioral preparation, system design drills, and high-frequency company questions for ${role}.</p>
        <div class="tags">
          <span class="tag">${role} Interview Prep</span>
          <span class="tag">STAR Method</span>
          <span class="tag">Portfolio Live Demo</span>
          <span class="tag">Offer Negotiation</span>
        </div>
      </div>
    </div>
  `;
}
