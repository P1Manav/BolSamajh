// BolSamajh Web Client — Studio & Voice Intelligence Engine

document.addEventListener('DOMContentLoaded', () => {
  // ==========================================
  // 1. STATE & GLOBAL CONFIG
  // ==========================================
  let currentApiKey = '';
  let currentPlayingAudio = null;
  let activeScript = 'natural';
  let dictationHistory = [];
  let deferredPwaPrompt = null;

  // Restore API key & history from localStorage if available
  try {
    currentApiKey = localStorage.getItem('bolsamajh_api_key') || '';
    const savedHistory = localStorage.getItem('bolsamajh_dictation_history');
    if (savedHistory) dictationHistory = JSON.parse(savedHistory);
  } catch (e) {}

  // ==========================================
  // 2. DOM ELEMENTS
  // ==========================================
  // Tabs & Nav
  const mainTabs = document.querySelectorAll('#mainTabs .nav-tab');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const pwaInstallBtn = document.getElementById('pwaInstallBtn');
  const mobileInstallPwaBtn = document.getElementById('mobileInstallPwaBtn');
  const sttStatusText = document.getElementById('sttStatusText');
  const apiKeyContainer = document.getElementById('apiKeyContainer');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const setApiKeyBtn = document.getElementById('setApiKeyBtn');
  const apiKeyBadge = document.getElementById('apiKeyBadge');
  const authAlertBanner = document.getElementById('authAlertBanner');
  const authAlertText = document.getElementById('authAlertText');
  const dismissAuthAlertBtn = document.getElementById('dismissAuthAlertBtn');

  // Overlay Controls
  const toggleOverlayBtn = document.getElementById('toggleOverlayBtn');
  const overlayBtnText = document.getElementById('overlayBtnText');
  const overlayDot = document.getElementById('overlayDot');
  const overlayHeroToggleBtn = document.getElementById('overlayHeroToggleBtn');
  const overlayHeroBtnText = document.getElementById('overlayHeroBtnText');
  const overlayCalloutBadge = document.getElementById('overlayCalloutBadge');

  // Tab 1: Dictation Studio
  const dictateMicBtn = document.getElementById('dictateMicBtn');
  const dictateWaveform = document.getElementById('dictateWaveform');
  const dictateStatusText = document.getElementById('dictateStatusText');
  const scriptPills = document.querySelectorAll('.script-pill');
  const dictateFillerCheck = document.getElementById('dictateFillerCheck');
  const dictateResultText = document.getElementById('dictateResultText');
  const dictateLatencyChip = document.getElementById('dictateLatencyChip');
  const dictateFillerChip = document.getElementById('dictateFillerChip');
  const dictateDurationChip = document.getElementById('dictateDurationChip');
  const dictateInjectBtn = document.getElementById('dictateInjectBtn');
  const dictateCopyBtn = document.getElementById('dictateCopyBtn');
  const dictateSendActionsBtn = document.getElementById('dictateSendActionsBtn');
  const dictateClearBtn = document.getElementById('dictateClearBtn');
  const dictateHistoryFeed = document.getElementById('dictateHistoryFeed');
  const clearDictateHistoryBtn = document.getElementById('clearDictateHistoryBtn');

  // Tab 2: Doc Intelligence
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');
  const urlInput = document.getElementById('urlInput');
  const loadUrlBtn = document.getElementById('loadUrlBtn');
  const docInfoCard = document.getElementById('docInfoCard');
  const docTitle = document.getElementById('docTitle');
  const docMeta = document.getElementById('docMeta');
  const docBadge = document.getElementById('docBadge');
  const clearDocBtn = document.getElementById('clearDocBtn');
  const langSelect = document.getElementById('langSelect');
  const chatFeed = document.getElementById('chatFeed');
  const textQueryInput = document.getElementById('textQueryInput');
  const sendBtn = document.getElementById('sendBtn');
  const docMicBtn = document.getElementById('micBtn');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const audioVisualizer = document.getElementById('audioVisualizer');
  const latencyPill = document.getElementById('latencyPill');

  // Tab 3: Voice Actions
  const commandInputText = document.getElementById('commandInputText');
  const customCommandInput = document.getElementById('customCommandInput');
  const runCommandBtn = document.getElementById('runCommandBtn');
  const commandOutput = document.getElementById('commandOutput');
  const actionInjectBtn = document.getElementById('actionInjectBtn');
  const actionCopyBtn = document.getElementById('actionCopyBtn');
  const commandChips = document.querySelectorAll('.command-chips .chip');

  // Tab 4: Android Companion
  const mobileQrCanvas = document.getElementById('mobileQrCanvas');
  const mobileLanUrl = document.getElementById('mobileLanUrl');
  const copyMobileUrlBtn = document.getElementById('copyMobileUrlBtn');

  // Tab 5: System Status
  const sysSttName = document.getElementById('sysSttName');
  const sysSttDevice = document.getElementById('sysSttDevice');
  const sysLlmName = document.getElementById('sysLlmName');
  const sysLlmFallback = document.getElementById('sysLlmFallback');
  const sysLlmTag = document.getElementById('sysLlmTag');
  const sysTtsName = document.getElementById('sysTtsName');
  const hkDictation = document.getElementById('hkDictation');
  const hkVoiceCommand = document.getElementById('hkVoiceCommand');
  const hkDocQa = document.getElementById('hkDocQa');
  const hkDocLoad = document.getElementById('hkDocLoad');

  // ==========================================
  // 3. TOAST NOTIFICATIONS & API KEY HELPERS
  // ==========================================
  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  function setApiKey(key) {
    currentApiKey = (key || '').trim();
    try {
      if (currentApiKey) localStorage.setItem('bolsamajh_api_key', currentApiKey);
      else localStorage.removeItem('bolsamajh_api_key');
    } catch (e) {}

    if (currentApiKey) {
      if (apiKeyBadge) apiKeyBadge.style.display = 'inline-block';
      if (apiKeyContainer) apiKeyContainer.classList.remove('auth-error');
      hideAuthError();
      showToast('API Key configured.', 'success');
    } else {
      if (apiKeyBadge) apiKeyBadge.style.display = 'none';
    }
  }

  if (currentApiKey && apiKeyInput) {
    apiKeyInput.value = currentApiKey;
    if (apiKeyBadge) apiKeyBadge.style.display = 'inline-block';
  }

  if (setApiKeyBtn) {
    setApiKeyBtn.addEventListener('click', () => setApiKey(apiKeyInput.value));
  }
  if (apiKeyInput) {
    apiKeyInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') setApiKey(apiKeyInput.value);
    });
  }
  if (dismissAuthAlertBtn) {
    dismissAuthAlertBtn.addEventListener('click', hideAuthError);
  }

  function showAuthError(msg) {
    if (authAlertBanner) {
      if (authAlertText) {
        authAlertText.textContent = msg || '⚠️ Authentication required (HTTP 401). Please enter your BOLSAMAJH_API_KEY in the top bar.';
      }
      authAlertBanner.style.display = 'flex';
    }
    if (apiKeyContainer) apiKeyContainer.classList.add('auth-error');
    if (apiKeyInput) apiKeyInput.focus();
  }

  function hideAuthError() {
    if (authAlertBanner) authAlertBanner.style.display = 'none';
    if (apiKeyContainer) apiKeyContainer.classList.remove('auth-error');
  }

  async function fetchWithAuth(url, options = {}) {
    options.headers = options.headers || {};
    if (currentApiKey) {
      if (options.headers instanceof Headers) {
        options.headers.set('Authorization', `Bearer ${currentApiKey}`);
      } else {
        options.headers['Authorization'] = `Bearer ${currentApiKey}`;
      }
    }
    const res = await fetch(url, options);
    if (res.status === 401) {
      showAuthError('⚠️ HTTP 401 Unauthorized: BOLSAMAJH_API_KEY is required for this action.');
    }
    return res;
  }

  // ==========================================
  // 4. TAB NAVIGATION
  // ==========================================
  function switchTab(tabId) {
    mainTabs.forEach((tab) => {
      const match = tab.dataset.tab === tabId;
      tab.classList.toggle('active', match);
      tab.setAttribute('aria-selected', match);
    });

    tabPanes.forEach((pane) => {
      pane.classList.toggle('active', pane.id === `view-${tabId}`);
    });

    window.location.hash = tabId;
  }

  mainTabs.forEach((tab) => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Handle URL hash on load
  const hash = window.location.hash.replace('#', '');
  if (['dashboard', 'dictate', 'doc', 'actions', 'webcall', 'history', 'why', 'benchmark', 'settings', 'mobile', 'system'].includes(hash)) {
    switchTab(hash);
  } else {
    switchTab('dashboard');
  }

  // ==========================================
  // 5. AUDIO VISUALIZER ENGINE
  // ==========================================
  let audioCtx = null;
  let animFrameId = null;

  function createVisualizer(canvas, stream) {
    if (!canvas) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!audioCtx || audioCtx.state === 'closed') {
        audioCtx = new AudioContextClass();
      }
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      const ctx = canvas.getContext('2d');

      function draw() {
        animFrameId = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const barWidth = (canvas.width / bufferLength) * 1.8;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * canvas.height * 0.85;
          const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
          gradient.addColorStop(0, '#6366f1');
          gradient.addColorStop(1, '#06b6d4');

          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.roundRect(x, canvas.height - barHeight, Math.max(3, barWidth - 2), barHeight, 3);
          ctx.fill();

          x += barWidth + 2;
        }
      }
      draw();
    } catch (e) {
      console.warn('Audio visualizer init error:', e);
    }
  }

  function stopVisualizer(canvas) {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  function interruptSpeech() {
    if (currentPlayingAudio) {
      currentPlayingAudio.pause();
      currentPlayingAudio.currentTime = 0;
      currentPlayingAudio = null;
      showToast('Speech playback interrupted.', 'info');
    }
  }

  // ==========================================
  // 6. TAB 1: DICTATION STUDIO
  // ==========================================
  let isDictating = false;
  let dictateMediaRecorder = null;
  let dictateAudioChunks = [];
  let dictatePressStartTime = 0;
  let isDictateHold = false;

  // Script selection
  scriptPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      scriptPills.forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      activeScript = pill.dataset.script;
    });
  });

  // Dictate Mic Button Events
  if (dictateMicBtn) {
    dictateMicBtn.addEventListener('click', () => {
      if (!isDictateHold) toggleDictateRecording();
      isDictateHold = false;
    });

    dictateMicBtn.addEventListener('mousedown', () => {
      dictatePressStartTime = Date.now();
    });

    dictateMicBtn.addEventListener('mouseup', () => {
      const duration = Date.now() - dictatePressStartTime;
      if (isDictating && duration > 400) {
        isDictateHold = true;
        stopDictateRecording();
      }
    });

    // Touch support for Android mobile companion
    dictateMicBtn.addEventListener('touchstart', (e) => {
      dictatePressStartTime = Date.now();
    }, { passive: true });

    dictateMicBtn.addEventListener('touchend', (e) => {
      const duration = Date.now() - dictatePressStartTime;
      if (isDictating && duration > 400) {
        isDictateHold = true;
        stopDictateRecording();
      }
    });
  }

  async function toggleDictateRecording() {
    if (!isDictating) startDictateRecording();
    else stopDictateRecording();
  }

  async function startDictateRecording() {
    interruptSpeech();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      dictateAudioChunks = [];
      dictateMediaRecorder = new MediaRecorder(stream);

      dictateMediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) dictateAudioChunks.push(e.data);
      };

      dictateMediaRecorder.onstop = handleDictationAudio;
      dictateMediaRecorder.start();
      isDictating = true;

      dictateMicBtn.classList.add('recording');
      dictateStatusText.innerText = '🔴 Listening... (speak in Hinglish, Hindi, or English)';
      createVisualizer(dictateWaveform, stream);
    } catch (err) {
      showToast(`Microphone access error: ${err.message}`, 'error');
    }
  }

  function stopDictateRecording() {
    if (dictateMediaRecorder && isDictating) {
      dictateMediaRecorder.stop();
      dictateMediaRecorder.stream.getTracks().forEach((track) => track.stop());
      isDictating = false;
      dictateMicBtn.classList.remove('recording');
      stopVisualizer(dictateWaveform);
      dictateStatusText.innerText = 'Transcribing and cleaning speech...';
    }
  }

  async function handleDictationAudio() {
    const audioBlob = new Blob(dictateAudioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('file', audioBlob, 'dictation.webm');
    formData.append('script', activeScript);
    formData.append('remove_fillers', dictateFillerCheck ? dictateFillerCheck.checked : true);

    try {
      const res = await fetchWithAuth('/api/dictate', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Dictation failed');

      dictateResultText.value = data.clean_text;
      dictateLatencyChip.innerText = `⚡ ${data.latency_ms} ms`;
      dictateFillerChip.innerText = `🧹 ${data.fillers_removed} fillers removed`;
      dictateDurationChip.innerText = `⏱️ ${data.duration_seconds}s audio`;
      dictateStatusText.innerText = 'Click mic to dictate again (or hold)';

      // Save to history
      addDictationToHistory({
        text: data.clean_text,
        script: data.script,
        fillers: data.fillers_removed,
        latency: data.latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });

      showToast('Transcription ready!', 'success');
    } catch (err) {
      dictateStatusText.innerText = `⚠️ Error: ${err.message}`;
      showToast(`Dictation Error: ${err.message}`, 'error');
    }
  }

  // Inject into active window
  if (dictateInjectBtn) {
    dictateInjectBtn.addEventListener('click', async () => {
      const text = dictateResultText.value.trim();
      if (!text) {
        showToast('Please dictate or type text first', 'info');
        return;
      }
      try {
        const res = await fetchWithAuth('/api/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          showToast('🚀 Text injected into active desktop app!', 'success');
        } else {
          showToast(`Injection failed: ${data.message}`, 'error');
        }
      } catch (e) {
        showToast(`Injection error: ${e.message}`, 'error');
      }
    });
  }

  // Copy to clipboard
  if (dictateCopyBtn) {
    dictateCopyBtn.addEventListener('click', () => {
      const text = dictateResultText.value.trim();
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => {
        showToast('📋 Copied to clipboard!', 'success');
      });
    });
  }

  // Send to Actions tab
  if (dictateSendActionsBtn) {
    dictateSendActionsBtn.addEventListener('click', () => {
      const text = dictateResultText.value.trim();
      if (!text) return;
      commandInputText.value = text;
      switchTab('actions');
      showToast('Sent to Voice Actions for transformation.', 'info');
    });
  }

  // Clear text
  if (dictateClearBtn) {
    dictateClearBtn.addEventListener('click', () => {
      dictateResultText.value = '';
      dictateLatencyChip.innerText = '⚡ 0 ms';
      dictateFillerChip.innerText = '🧹 0 fillers cleaned';
      dictateDurationChip.innerText = '⏱️ 0.0s audio';
    });
  }

  // History Management
  function addDictationToHistory(item) {
    dictationHistory.unshift(item);
    if (dictationHistory.length > 20) dictationHistory.pop();
    try {
      localStorage.setItem('bolsamajh_dictation_history', JSON.stringify(dictationHistory));
    } catch (e) {}
    renderDictationHistory();
  }

  function renderDictationHistory() {
    if (!dictateHistoryFeed) return;
    if (dictationHistory.length === 0) {
      dictateHistoryFeed.innerHTML = '<div class="history-empty">No dictations yet in this session. Tap mic above to start!</div>';
      return;
    }
    dictateHistoryFeed.innerHTML = '';
    dictationHistory.forEach((item, index) => {
      const card = document.createElement('div');
      card.className = 'history-item-card';
      card.innerHTML = `
        <div class="history-text" title="${escapeHtml(item.text)}">
          <span class="pill-badge">${escapeHtml(item.script || 'mixed')}</span>
          <span style="color:var(--text-dim); font-size:0.75rem;">${item.timestamp}</span>
          <strong>${escapeHtml(item.text)}</strong>
        </div>
        <div class="history-actions">
          <button class="btn btn-secondary btn-sm" data-idx="${index}" data-action="inject" title="Inject to active window">🚀</button>
          <button class="btn btn-secondary btn-sm" data-idx="${index}" data-action="copy" title="Copy text">📋</button>
        </div>
      `;
      dictateHistoryFeed.appendChild(card);
    });
  }

  if (dictateHistoryFeed) {
    dictateHistoryFeed.addEventListener('click', async (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;
      const idx = parseInt(btn.dataset.idx, 10);
      const action = btn.dataset.action;
      const item = dictationHistory[idx];
      if (!item) return;

      if (action === 'copy') {
        navigator.clipboard.writeText(item.text).then(() => showToast('Copied to clipboard!', 'success'));
      } else if (action === 'inject') {
        try {
          const res = await fetchWithAuth('/api/inject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: item.text }),
          });
          const d = await res.json();
          if (d.status === 'ok') showToast('🚀 Injected into active app!', 'success');
        } catch (err) {
          showToast(`Inject error: ${err.message}`, 'error');
        }
      }
    });
  }

  if (clearDictateHistoryBtn) {
    clearDictateHistoryBtn.addEventListener('click', () => {
      dictationHistory = [];
      try {
        localStorage.removeItem('bolsamajh_dictation_history');
      } catch (e) {}
      renderDictationHistory();
      showToast('History cleared', 'info');
    });
  }

  renderDictationHistory();

  // ==========================================
  // 7. TAB 2: DOC INTELLIGENCE (TALK TO DOC)
  // ==========================================
  if (browseBtn) browseBtn.addEventListener('click', () => fileInput.click());
  if (fileInput) fileInput.addEventListener('change', handleFileUpload);

  if (dropzone) {
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('drag-over');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('drag-over');
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    });
  }

  function handleFileUpload(e) {
    if (e.target.files.length) handleFiles(e.target.files);
  }

  async function handleFiles(files) {
    const file = files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setDocLoading(true, 'Uploading and indexing document…');
    try {
      const res = await fetchWithAuth('/api/document/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      updateDocCard(data);
      addSystemMessage(`Document indexed: "${data.title}" (${data.num_pages} pages, ${data.num_chunks} chunks).`);
      showToast(`Loaded: ${data.title}`, 'success');
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    } finally {
      setDocLoading(false);
    }
  }

  if (loadUrlBtn) {
    loadUrlBtn.addEventListener('click', async () => {
      const url = urlInput.value.trim();
      if (!url) return;

      setDocLoading(true, 'Fetching and indexing URL…');
      try {
        const res = await fetchWithAuth('/api/document/url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to index URL');

        updateDocCard(data);
        addSystemMessage(`Webpage indexed: "${data.title}" (${data.num_chunks} sections).`);
        showToast('URL indexed successfully', 'success');
      } catch (err) {
        showToast(`URL error: ${err.message}`, 'error');
      } finally {
        setDocLoading(false);
      }
    });
  }

  if (clearDocBtn) {
    clearDocBtn.addEventListener('click', async () => {
      try {
        await fetchWithAuth('/api/document', { method: 'DELETE' });
        docInfoCard.style.display = 'none';
        dropzone.style.display = 'block';
        docBadge.innerText = 'No doc loaded';
        docBadge.classList.remove('loaded');
        showToast('Active document cleared', 'info');
      } catch (e) {
        showToast('Failed to clear document', 'error');
      }
    });
  }

  function updateDocCard(data) {
    docTitle.innerText = data.title || 'Indexed Document';
    docMeta.innerText = `${data.num_pages || 1} pages • ${data.num_chunks || 0} indexed chunks`;
    docInfoCard.style.display = 'flex';
    dropzone.style.display = 'none';
    docBadge.innerText = 'Document Loaded';
    docBadge.classList.add('loaded');
  }

  function setDocLoading(isLoading, msg) {
    if (isLoading) {
      docBadge.innerText = 'Indexing…';
      if (latencyPill) latencyPill.innerText = msg || 'Indexing…';
    } else {
      if (latencyPill) latencyPill.innerText = 'Ready';
    }
  }

  // Chat Submissions (Text and Voice)
  if (sendBtn) sendBtn.addEventListener('click', handleTextQuery);
  if (textQueryInput) {
    textQueryInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleTextQuery();
    });
  }

  // Sample Chips
  document.querySelectorAll('.sample-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      if (textQueryInput) textQueryInput.value = chip.dataset.q;
      handleTextQuery();
    });
  });

  async function handleTextQuery() {
    const q = textQueryInput.value.trim();
    if (!q) return;

    textQueryInput.value = '';
    addUserMessage(q);
    if (clearHistoryBtn) clearHistoryBtn.style.display = 'inline-block';
    const assistantRow = addAssistantLoadingMessage();

    try {
      const res = await fetchWithAuth('/api/qa/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, language: langSelect.value }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let fullText = '';
      const bubble = assistantRow.querySelector('.message-bubble');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const dataStr = trimmed.slice(5).trim();
          if (dataStr === '[DONE]') continue;

          try {
            const dataObj = JSON.parse(dataStr);
            if (dataObj.token) {
              fullText += dataObj.token;
              bubble.innerText = fullText;
              chatFeed.scrollTop = chatFeed.scrollHeight;
            }
            if (dataObj.citations && Array.isArray(dataObj.citations)) {
              renderCitations(assistantRow, dataObj.citations);
            }
          } catch (e) {}
        }
      }

      // Add Interrupt and TTS play options
      addAudioControls(assistantRow, fullText, langSelect.value);
    } catch (err) {
      assistantRow.querySelector('.message-bubble').innerText = `⚠️ Error: ${err.message}`;
      showToast(`Q&A Error: ${err.message}`, 'error');
    }
  }

  // Voice Recording in Doc Tab
  let isDocRecording = false;
  let docMediaRecorder = null;
  let docAudioChunks = [];

  if (docMicBtn) {
    docMicBtn.addEventListener('click', toggleDocRecording);
  }

  async function toggleDocRecording() {
    if (!isDocRecording) {
      interruptSpeech();
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        docAudioChunks = [];
        docMediaRecorder = new MediaRecorder(stream);
        docMediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) docAudioChunks.push(e.data);
        };
        docMediaRecorder.onstop = handleDocVoiceRecorded;
        docMediaRecorder.start();
        isDocRecording = true;
        docMicBtn.classList.add('recording');
        if (audioVisualizer) {
          audioVisualizer.style.display = 'block';
          createVisualizer(audioVisualizer, stream);
        }
      } catch (err) {
        showToast(`Mic access denied: ${err.message}`, 'error');
      }
    } else {
      if (docMediaRecorder && isDocRecording) {
        docMediaRecorder.stop();
        docMediaRecorder.stream.getTracks().forEach((track) => track.stop());
        isDocRecording = false;
        docMicBtn.classList.remove('recording');
        if (audioVisualizer) {
          audioVisualizer.style.display = 'none';
          stopVisualizer(audioVisualizer);
        }
      }
    }
  }

  async function handleDocVoiceRecorded() {
    const audioBlob = new Blob(docAudioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('language', langSelect.value);

    addUserMessage('🎤 Voice question submitted...');
    const assistantRow = addAssistantLoadingMessage();

    try {
      const res = await fetchWithAuth('/api/qa/voice', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Voice processing failed');

      // Update user message bubble
      const userRows = document.querySelectorAll('.message-row.user');
      if (userRows.length) {
        userRows[userRows.length - 1].querySelector('.message-bubble').innerText = `🎤 "${data.question}"`;
      }

      updateAssistantMessage(assistantRow, data);
    } catch (err) {
      assistantRow.querySelector('.message-bubble').innerText = `⚠️ ${err.message}`;
      showToast(`Voice QA Error: ${err.message}`, 'error');
    }
  }

  function addAudioControls(row, text, lang) {
    if (!text || text.startsWith('⚠️')) return;
    const actionsRow = document.createElement('div');
    actionsRow.className = 'audio-player-row';

    const speakBtn = document.createElement('button');
    speakBtn.className = 'btn btn-secondary btn-sm';
    speakBtn.innerHTML = '🔊 Speak Answer';

    const interruptBtn = document.createElement('button');
    interruptBtn.className = 'btn btn-secondary btn-sm';
    interruptBtn.innerHTML = '⏹️ Interrupt';
    interruptBtn.style.display = 'none';

    actionsRow.appendChild(speakBtn);
    actionsRow.appendChild(interruptBtn);
    row.appendChild(actionsRow);

    speakBtn.addEventListener('click', async () => {
      interruptSpeech();
      speakBtn.innerText = '⏳ Synthesizing…';
      try {
        const res = await fetchWithAuth('/v1/audio/speech', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: text, voice: lang === 'gujarati' ? 'gu-IN-DhwaniNeural' : 'hi-IN-SwaraNeural' }),
        });
        if (!res.ok) throw new Error(`TTS failed (${res.status})`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        currentPlayingAudio = audio;

        interruptBtn.style.display = 'inline-block';
        speakBtn.style.display = 'none';

        audio.onended = () => {
          interruptBtn.style.display = 'none';
          speakBtn.style.display = 'inline-block';
          speakBtn.innerHTML = '🔊 Replay';
          currentPlayingAudio = null;
        };

        audio.play().catch(() => {});
      } catch (e) {
        showToast(`Audio error: ${e.message}`, 'error');
        speakBtn.innerHTML = '🔊 Speak Answer';
      }
    });

    interruptBtn.addEventListener('click', () => {
      interruptSpeech();
      interruptBtn.style.display = 'none';
      speakBtn.style.display = 'inline-block';
      speakBtn.innerHTML = '🔊 Speak Answer';
    });
  }

  function updateAssistantMessage(row, data) {
    const bubble = row.querySelector('.message-bubble');
    bubble.innerText = data.answer;

    if (data.citations && data.citations.length) {
      renderCitations(row, data.citations);
    }

    if (data.audio_url) {
      const audioRow = document.createElement('div');
      audioRow.className = 'audio-player-row';

      const audio = document.createElement('audio');
      audio.controls = true;
      audioRow.appendChild(audio);

      const interruptBtn = document.createElement('button');
      interruptBtn.className = 'btn btn-secondary btn-sm';
      interruptBtn.innerText = '⏹️ Stop';
      audioRow.appendChild(interruptBtn);
      row.appendChild(audioRow);

      fetchWithAuth(data.audio_url)
        .then(async (r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const blob = await r.blob();
          const blobUrl = URL.createObjectURL(blob);
          audio.src = blobUrl;
          currentPlayingAudio = audio;
          audio.autoplay = true;
          audio.play().catch(() => {});
        })
        .catch((err) => {
          const errSpan = document.createElement('span');
          errSpan.className = 'audio-err-msg';
          errSpan.innerText = `🔊 Audio unavailable (${err.message})`;
          audioRow.appendChild(errSpan);
        });

      interruptBtn.addEventListener('click', () => {
        interruptSpeech();
        audio.pause();
      });
    }

    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function renderCitations(row, citations) {
    if (!citations || !citations.length) return;
    let citContainer = row.querySelector('.citations-container');
    if (!citContainer) {
      citContainer = document.createElement('div');
      citContainer.className = 'citations-container';
      row.appendChild(citContainer);
    } else {
      citContainer.innerHTML = '';
    }

    citations.forEach((c) => {
      const pill = document.createElement('span');
      pill.className = 'citation-pill';
      const pct = c.score ? ` (${Math.round(c.score * 100)}%)` : '';
      pill.innerText = `📌 ${c.citation}${pct}`;
      if (c.text) pill.title = c.text;
      citContainer.appendChild(pill);
    });
  }

  function addUserMessage(text) {
    const wc = document.querySelector('.welcome-card');
    if (wc) wc.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function addAssistantLoadingMessage() {
    const wc = document.querySelector('.welcome-card');
    if (wc) wc.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = '<div class="message-bubble">⏳ Generating answer with citations...</div>';
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
    return row;
  }

  function addSystemMessage(text) {
    const wc = document.querySelector('.welcome-card');
    if (wc) wc.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `<div class="message-bubble" style="border-left: 3px solid var(--accent-cyan);">${escapeHtml(text)}</div>`;
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', () => {
      chatFeed.innerHTML = '';
      clearHistoryBtn.style.display = 'none';
      showToast('Conversation cleared', 'info');
    });
  }

  // ==========================================
  // 8. TAB 3: VOICE ACTIONS
  // ==========================================
  commandChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      if (customCommandInput) customCommandInput.value = chip.dataset.cmd;
      runCommand(chip.dataset.cmd);
    });
  });

  if (runCommandBtn) {
    runCommandBtn.addEventListener('click', () => {
      const cmd = customCommandInput.value.trim() || 'Make it formal and professional';
      runCommand(cmd);
    });
  }

  async function runCommand(command) {
    const text = commandInputText.value.trim();
    if (!text) {
      showToast('Please enter text to transform', 'info');
      return;
    }

    commandOutput.innerText = '⚡ Processing transformation with LLM…';
    actionInjectBtn.disabled = true;
    actionCopyBtn.disabled = true;

    try {
      const res = await fetchWithAuth('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, command }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Command failed');

      commandOutput.innerText = data.result;
      actionInjectBtn.disabled = false;
      actionCopyBtn.disabled = false;
      showToast('Text transformed!', 'success');
    } catch (err) {
      commandOutput.innerText = `Error: ${err.message}`;
      showToast(`Command error: ${err.message}`, 'error');
    }
  }

  if (actionInjectBtn) {
    actionInjectBtn.addEventListener('click', async () => {
      const text = commandOutput.innerText.trim();
      if (!text || text.startsWith('Error:')) return;
      try {
        const res = await fetchWithAuth('/api/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });
        const d = await res.json();
        if (d.status === 'ok') showToast('🚀 Injected transformed text into active app!', 'success');
      } catch (e) {
        showToast(`Inject failed: ${e.message}`, 'error');
      }
    });
  }

  if (actionCopyBtn) {
    actionCopyBtn.addEventListener('click', () => {
      const text = commandOutput.innerText.trim();
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard!', 'success'));
    });
  }

  // ==========================================
  // 9. TAB 4: ANDROID COMPANION & PWA
  // ==========================================
  if (copyMobileUrlBtn) {
    copyMobileUrlBtn.addEventListener('click', () => {
      const url = mobileLanUrl.innerText.trim();
      navigator.clipboard.writeText(url).then(() => showToast('Mobile URL copied!', 'success'));
    });
  }

  // Listen for PWA beforeinstallprompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPwaPrompt = e;
    if (pwaInstallBtn) pwaInstallBtn.style.display = 'inline-flex';
    if (mobileInstallPwaBtn) mobileInstallPwaBtn.style.display = 'block';
  });

  function triggerPwaInstall() {
    if (deferredPwaPrompt) {
      deferredPwaPrompt.prompt();
      deferredPwaPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          showToast('App installed!', 'success');
        }
        deferredPwaPrompt = null;
        if (pwaInstallBtn) pwaInstallBtn.style.display = 'none';
      });
    } else {
      showToast('To install: in Chrome tap ⋮ (Menu) -> Add to Home screen', 'info');
    }
  }

  if (pwaInstallBtn) pwaInstallBtn.addEventListener('click', triggerPwaInstall);
  if (mobileInstallPwaBtn) mobileInstallPwaBtn.addEventListener('click', triggerPwaInstall);

  // Register Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch((e) => console.log('SW registration note:', e));
  }

  // ==========================================
  // 10. SYSTEM STATUS & QR INITIALIZATION
  // ==========================================
  async function loadSystemStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();

      // Top bar indicator
      if (sttStatusText) {
        sttStatusText.innerText = `${data.device || 'Ready'} • ${data.stt || 'Faster-Whisper'}`;
      }

      // Tab 4: Mobile URL & QR
      const host = data.local_ip || window.location.hostname;
      const port = data.port || window.location.port || 8000;
      const mobileUrl = `http://${host}:${port}`;
      if (mobileLanUrl) mobileLanUrl.innerText = mobileUrl;

      if (mobileQrCanvas && window.renderQRCode) {
        window.renderQRCode(mobileUrl, mobileQrCanvas);
      }

      // Tab 5: System Diagnostics
      if (sysSttName) sysSttName.innerText = data.stt || 'Faster-Whisper';
      if (sysSttDevice) sysSttDevice.innerText = data.device || 'CUDA GPU';
      if (sysLlmName) sysLlmName.innerText = data.llm || 'Ollama Local';
      if (sysLlmFallback) sysLlmFallback.innerText = data.llm_fallback || 'Ready';
      if (sysLlmTag) {
        sysLlmTag.innerText = data.llm_ready ? 'Online' : 'Ready';
        sysLlmTag.className = data.llm_ready ? 'engine-status-tag ready' : 'engine-status-tag';
      }
      if (sysTtsName) sysTtsName.innerText = data.tts || 'Edge-TTS';

      // Tab 0: Welcome Dashboard System Cards
      const dashboardSttVal = document.getElementById('dashboardSttVal');
      const dashboardSttSub = document.getElementById('dashboardSttSub');
      const dashboardLlmVal = document.getElementById('dashboardLlmVal');
      const dashboardTtsVal = document.getElementById('dashboardTtsVal');
      const dashboardHardwareBadge = document.getElementById('dashboardHardwareBadge');
      const dashboardDocLoadedStatus = document.getElementById('dashboardDocLoadedStatus');
      const dashboardPrivacyBanner = document.getElementById('dashboardPrivacyBanner');

      const isLlmLocal = (data.llm || '').toLowerCase().includes('ollama');
      const isTtsLocal = (data.tts || '').toLowerCase().includes('piper');
      const isFullyOffline = isLlmLocal && isTtsLocal;

      if (dashboardPrivacyBanner) {
        if (isFullyOffline) {
          dashboardPrivacyBanner.className = 'privacy-banner privacy-offline';
          dashboardPrivacyBanner.innerHTML = '<span>🟢</span><span><strong>100% Air-Gapped Offline Mode:</strong> All Speech-to-Text, LLM Intelligence, and Voice Synthesis models are running locally on-device. Zero network traffic leaves this machine.</span>';
        } else {
          dashboardPrivacyBanner.className = 'privacy-banner privacy-hybrid';
          dashboardPrivacyBanner.innerHTML = `<span>🛡️</span><span><strong>System Architecture (Hybrid Mode):</strong> Speech-to-Text &amp; Document RAG run 100% locally on-device (${data.device || 'GPU'}). Voice synthesis uses ${data.tts || 'Edge-TTS'}. For air-gapped offline use, select Piper TTS in Settings.</span>`;
        }
      }

      if (dashboardSttVal) dashboardSttVal.innerHTML = `${data.stt || 'Faster-Whisper'} <span class="badge-local">Local</span>`;
      if (dashboardSttSub) dashboardSttSub.innerText = `${data.device || 'CUDA GPU'} • On-Device`;
      if (dashboardLlmVal) dashboardLlmVal.innerHTML = `${data.llm || 'LLM'} <span class="${isLlmLocal ? 'badge-local' : 'badge-cloud'}">${isLlmLocal ? 'Local' : 'Cloud API'}</span>`;
      if (dashboardTtsVal) dashboardTtsVal.innerHTML = `${data.tts || 'TTS'} <span class="${isTtsLocal ? 'badge-local' : 'badge-cloud'}">${isTtsLocal ? '100% Offline' : 'Cloud Endpoint'}</span>`;
      if (dashboardHardwareBadge) dashboardHardwareBadge.innerText = `${data.device || 'System'} Ready`;
      if (dashboardDocLoadedStatus) {
        dashboardDocLoadedStatus.innerText = data.document_loaded ? '✓ Document indexed & ready for Voice Q&A' : 'No document loaded';
        dashboardDocLoadedStatus.style.color = data.document_loaded ? '#10b981' : 'var(--text-muted)';
      }

      if (data.hotkeys) {
        if (hkDictation) hkDictation.innerText = (data.hotkeys.dictation || 'Alt+Shift+Space').toUpperCase();
        if (hkVoiceCommand) hkVoiceCommand.innerText = (data.hotkeys.voice_command || 'Alt+Shift+C').toUpperCase();
        if (hkDocQa) hkDocQa.innerText = (data.hotkeys.doc_qa || 'Alt+Shift+A').toUpperCase();
        if (hkDocLoad) hkDocLoad.innerText = (data.hotkeys.doc_load || 'Alt+Shift+D').toUpperCase();
      }
    } catch (e) {
      console.warn('System status fetch note:', e);
    }
  }

  // ==========================================
  // 11. OVERLAY HUD INTEGRATION
  // ==========================================
  async function checkOverlayStatus() {
    try {
      const res = await fetch('/api/overlay');
      if (!res.ok) return;
      const data = await res.json();
      updateOverlayUI(data.pinned);
    } catch (e) {}
  }

  function updateOverlayUI(isPinned) {
    if (toggleOverlayBtn) {
      toggleOverlayBtn.classList.toggle('active', isPinned);
    }
    if (overlayBtnText) {
      overlayBtnText.innerText = isPinned ? 'Overlay Active' : 'Start Overlay';
    }
    if (overlayHeroBtnText) {
      overlayHeroBtnText.innerText = isPinned ? 'Overlay Active (Hide)' : 'Start Overlay';
    }
    if (overlayCalloutBadge) {
      overlayCalloutBadge.innerText = isPinned ? 'Floating Pill: Active' : 'Floating Pill: Idle';
      overlayCalloutBadge.classList.toggle('active', isPinned);
    }

    // Dashboard Hero Activation Elements
    const dashboardOverlayDot = document.getElementById('dashboardOverlayDot');
    const dashboardOverlayStatusText = document.getElementById('dashboardOverlayStatusText');
    const dashboardOverlayActivateBtn = document.getElementById('dashboardOverlayActivateBtn');
    const dashboardOverlayActivateBtnText = document.getElementById('dashboardOverlayActivateBtnText');
    const overlayActivationBox = document.querySelector('.overlay-activation-box');

    if (dashboardOverlayDot) {
      dashboardOverlayDot.classList.toggle('live', isPinned);
    }
    if (dashboardOverlayStatusText) {
      dashboardOverlayStatusText.innerText = isPinned ? 'Overlay Active on Desktop' : 'Overlay Inactive';
      dashboardOverlayStatusText.style.color = isPinned ? '#10b981' : '#cbd5e1';
    }
    if (dashboardOverlayActivateBtn) {
      dashboardOverlayActivateBtn.classList.toggle('active', isPinned);
    }
    if (dashboardOverlayActivateBtnText) {
      dashboardOverlayActivateBtnText.innerText = isPinned ? 'Overlay Active (Click to Hide)' : 'Activate Desktop Overlay';
    }
    if (overlayActivationBox) {
      overlayActivationBox.classList.toggle('active', isPinned);
    }
  }

  async function toggleOverlay() {
    try {
      const res = await fetchWithAuth('/api/overlay/toggle', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'ok') {
        updateOverlayUI(data.pinned);
        showToast(data.message, data.pinned ? 'success' : 'info');
      } else {
        showToast(`Overlay error: ${data.message}`, 'error');
      }
    } catch (err) {
      showToast(`Overlay network error: ${err.message}`, 'error');
    }
  }

  if (toggleOverlayBtn) toggleOverlayBtn.addEventListener('click', toggleOverlay);
  if (overlayHeroToggleBtn) overlayHeroToggleBtn.addEventListener('click', toggleOverlay);

  // Tab 0: Welcome Dashboard Event Handlers
  const dashboardOverlayActivateBtn = document.getElementById('dashboardOverlayActivateBtn');
  if (dashboardOverlayActivateBtn) {
    dashboardOverlayActivateBtn.addEventListener('click', toggleOverlay);
  }

  // Dashboard Shortcut Creator
  const dashboardInstallShortcutsBtn = document.getElementById('dashboardInstallShortcutsBtn');
  if (dashboardInstallShortcutsBtn) {
    dashboardInstallShortcutsBtn.addEventListener('click', async () => {
      try {
        dashboardInstallShortcutsBtn.disabled = true;
        dashboardInstallShortcutsBtn.innerText = 'Creating Shortcut...';
        const res = await fetchWithAuth('/api/install-shortcuts', { method: 'POST' });
        const data = await res.json();
        showToast(data.message, data.status === 'ok' ? 'success' : 'error');
      } catch (err) {
        showToast(`Shortcut error: ${err.message}`, 'error');
      } finally {
        dashboardInstallShortcutsBtn.disabled = false;
        dashboardInstallShortcutsBtn.innerHTML = '<span>📌</span> Add Desktop Shortcut';
      }
    });
  }

  // Switch tab buttons
  document.querySelectorAll('[data-switch-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-switch-tab');
      if (target) switchTab(target);
    });
  });

  // Dashboard Quick Mic Test
  const dashboardQuickMicBtn = document.getElementById('dashboardQuickMicBtn');
  const dashboardQuickMicBtnText = document.getElementById('dashboardQuickMicBtnText');
  const dashboardQuickMicStatus = document.getElementById('dashboardQuickMicStatus');
  const dashboardQuickMicResult = document.getElementById('dashboardQuickMicResult');
  let dashboardMicRecording = false;
  let dashboardMediaRecorder = null;
  let dashboardAudioChunks = [];

  if (dashboardQuickMicBtn) {
    dashboardQuickMicBtn.addEventListener('click', async () => {
      if (!dashboardMicRecording) {
        // Start recording
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          dashboardMediaRecorder = new MediaRecorder(stream);
          dashboardAudioChunks = [];
          dashboardMediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) dashboardAudioChunks.push(e.data);
          };
          dashboardMediaRecorder.onstop = async () => {
            stream.getTracks().forEach((track) => track.stop());
            if (dashboardAudioChunks.length === 0) return;
            const audioBlob = new Blob(dashboardAudioChunks, { type: 'audio/webm' });
            if (dashboardQuickMicStatus) dashboardQuickMicStatus.innerText = 'Transcribing...';
            try {
              const formData = new FormData();
              formData.append('file', audioBlob, 'quick_test.webm');
              formData.append('script', activeScript);
              formData.append('strip_fillers', 'true');
              const res = await fetchWithAuth('/api/dictate', { method: 'POST', body: formData });
              const data = await res.json();
              if (data.status === 'ok') {
                if (dashboardQuickMicResult) dashboardQuickMicResult.innerText = `"${data.text}"`;
                if (dashboardQuickMicStatus) dashboardQuickMicStatus.innerText = `Ready (${data.latency_ms || 0} ms)`;
                showToast('Transcription successful!', 'success');
              } else {
                if (dashboardQuickMicStatus) dashboardQuickMicStatus.innerText = 'Error';
                showToast(`Dictation error: ${data.detail || data.message}`, 'error');
              }
            } catch (err) {
              if (dashboardQuickMicStatus) dashboardQuickMicStatus.innerText = 'Failed';
              showToast(`Network error: ${err.message}`, 'error');
            }
          };
          dashboardMediaRecorder.start();
          dashboardMicRecording = true;
          if (dashboardQuickMicBtnText) dashboardQuickMicBtnText.innerText = 'Stop & Transcribe';
          if (dashboardQuickMicStatus) dashboardQuickMicStatus.innerText = 'Listening... Speak now';
          dashboardQuickMicBtn.classList.add('btn-danger');
        } catch (err) {
          showToast(`Microphone permission error: ${err.message}`, 'error');
        }
      } else {
        // Stop recording
        if (dashboardMediaRecorder && dashboardMediaRecorder.state !== 'inactive') {
          dashboardMediaRecorder.stop();
        }
        dashboardMicRecording = false;
        if (dashboardQuickMicBtnText) dashboardQuickMicBtnText.innerText = 'Test Speaking Here';
        dashboardQuickMicBtn.classList.remove('btn-danger');
      }
    });
  }

  // Dashboard Dropzone
  const dashboardDropzone = document.getElementById('dashboardDropzone');
  const dashboardFileInput = document.getElementById('dashboardFileInput');
  if (dashboardDropzone && dashboardFileInput) {
    dashboardDropzone.addEventListener('click', () => dashboardFileInput.click());
    dashboardFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileUpload(e.target.files[0]);
        switchTab('doc');
      }
    });
    dashboardDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dashboardDropzone.classList.add('dragover');
    });
    dashboardDropzone.addEventListener('dragleave', () => dashboardDropzone.classList.remove('dragover'));
    dashboardDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dashboardDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileUpload(e.dataTransfer.files[0]);
        switchTab('doc');
      }
    });
  }

  // Dashboard Sample Action Chips
  const dashboardActionSampleInput = document.getElementById('dashboardActionSampleInput');
  const dashboardActionResult = document.getElementById('dashboardActionResult');
  document.querySelectorAll('.chip-action').forEach((chip) => {
    chip.addEventListener('click', async () => {
      const text = (dashboardActionSampleInput ? dashboardActionSampleInput.value : '').trim();
      const instruction = chip.getAttribute('data-sample-cmd') || '';
      if (!text || !instruction) return;
      if (dashboardActionResult) dashboardActionResult.innerText = 'Transforming with local intelligence...';
      try {
        const formData = new FormData();
        formData.append('instruction', instruction);
        formData.append('selected_text', text);
        const res = await fetchWithAuth('/api/command', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.status === 'ok') {
          if (dashboardActionResult) dashboardActionResult.innerText = `"${data.result_text}"`;
        } else {
          if (dashboardActionResult) dashboardActionResult.innerText = `Error: ${data.detail || data.message}`;
        }
      } catch (err) {
        if (dashboardActionResult) dashboardActionResult.innerText = `Network error: ${err.message}`;
      }
    });
  });

  // ==========================================
  // 12. TAB: WEB CALL (FULL-DUPLEX VOICE)
  // ==========================================
  let webcallWs = null;
  let webcallMediaStream = null;
  let webcallAudioContext = null;
  let webcallProcessor = null;
  let webcallActiveGenId = null;
  let webcallAudioQueue = [];
  let webcallCurrentAudio = null;
  let webcallIsCalling = false;

  const webcallStartBtn = document.getElementById('webcallStartBtn');
  const webcallStopBtn = document.getElementById('webcallStopBtn');
  const webcallMuteBtn = document.getElementById('webcallMuteBtn');
  const webcallStateDot = document.querySelector('.webcall-state-dot');
  const webcallStateText = document.getElementById('webcallStateText');
  const webcallTranscript = document.getElementById('webcallTranscript');
  const webcallWaveform = document.getElementById('webcallWaveform');
  const webcallLangSelect = document.getElementById('webcallLangSelect');
  const webcallDocStatus = document.getElementById('webcallDocStatus');
  const webcallUploadBtn = document.getElementById('webcallUploadBtn');
  const webcallFileInput = document.getElementById('webcallFileInput');

  function setWebcallState(state, text) {
    if (webcallStateDot) {
      webcallStateDot.className = `webcall-state-dot ${state}`;
    }
    if (webcallStateText) {
      webcallStateText.innerText = text || (state.charAt(0).toUpperCase() + state.slice(1));
    }
  }

  function appendWebcallMessage(role, text, citations = []) {
    if (!webcallTranscript) return;
    const welcome = webcallTranscript.querySelector('.webcall-welcome');
    if (welcome) welcome.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `webcall-msg ${role}`;
    let html = `<div>${escapeHtml(text)}</div>`;
    if (citations && citations.length > 0) {
      html += '<div style="margin-top:6px;">';
      citations.forEach((cit) => {
        html += `<span class="citation-chip">📑 ${escapeHtml(cit)}</span>`;
      });
      html += '</div>';
    }
    msgDiv.innerHTML = html;
    webcallTranscript.appendChild(msgDiv);
    webcallTranscript.scrollTop = webcallTranscript.scrollHeight;

    // Add to session history
    dictationHistory.unshift({
      type: 'qa',
      role,
      text,
      time: new Date().toLocaleTimeString(),
      citations: citations || [],
    });
    renderHistoryTab();
  }

  function playNextWebcallAudio() {
    if (webcallCurrentAudio || webcallAudioQueue.length === 0) return;
    const item = webcallAudioQueue.shift();
    if (item.genId !== webcallActiveGenId) {
      playNextWebcallAudio();
      return;
    }
    const audio = new Audio('data:audio/mp3;base64,' + item.b64);
    webcallCurrentAudio = audio;
    setWebcallState('speaking', 'Speaking response...');

    audio.onended = () => {
      webcallCurrentAudio = null;
      if (webcallAudioQueue.length > 0) {
        playNextWebcallAudio();
      } else {
        setWebcallState('idle', 'Listening for next question...');
      }
    };
    audio.onerror = () => {
      webcallCurrentAudio = null;
      playNextWebcallAudio();
    };
    audio.play().catch(() => {
      webcallCurrentAudio = null;
      playNextWebcallAudio();
    });
  }

  function stopWebcallAudioPlayback() {
    if (webcallCurrentAudio) {
      try { webcallCurrentAudio.pause(); } catch (e) {}
      webcallCurrentAudio = null;
    }
    webcallAudioQueue = [];
  }

  function triggerWebcallBargeIn() {
    if (webcallCurrentAudio || webcallAudioQueue.length > 0) {
      stopWebcallAudioPlayback();
      if (webcallWs && webcallWs.readyState === WebSocket.OPEN) {
        webcallWs.send(JSON.stringify({
          type: 'barge_in',
          generation_id: webcallActiveGenId,
        }));
      }
      setWebcallState('listening', 'Interrupted — listening...');
    }
  }

  async function startWebCall() {
    if (webcallIsCalling) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, sampleRate: 16000, echoCancellation: true, noiseSuppression: true },
      });
      webcallMediaStream = stream;
      createVisualizer(webcallWaveform, stream);

      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${proto}//${window.location.host}/ws/call?lang=${encodeURIComponent(webcallLangSelect ? webcallLangSelect.value : 'hinglish')}`;
      webcallWs = new WebSocket(wsUrl);

      webcallWs.onopen = () => {
        webcallIsCalling = true;
        if (webcallStartBtn) webcallStartBtn.style.display = 'none';
        if (webcallStopBtn) webcallStopBtn.style.display = 'inline-flex';
        if (webcallMuteBtn) webcallMuteBtn.style.display = 'inline-flex';
        setWebcallState('idle', 'Connected — Speak anytime');

        // Set up Web Audio PCM capture
        const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
        webcallAudioContext = new AudioCtxClass({ sampleRate: 16000 });
        const source = webcallAudioContext.createMediaStreamSource(stream);
        webcallProcessor = webcallAudioContext.createScriptProcessor(4096, 1, 1);

        let silenceCount = 0;
        let isSpeakingNow = false;

        webcallProcessor.onaudioprocess = (e) => {
          if (!webcallWs || webcallWs.readyState !== WebSocket.OPEN) return;
          const input = e.inputBuffer.getChannelData(0);

          // Calculate RMS for client-side VAD & barge-in
          let sum = 0;
          const pcm16 = new Int16Array(input.length);
          for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            sum += s * s;
          }
          const rms = Math.sqrt(sum / input.length);

          if (rms > 0.035) {
            // Speech detected
            silenceCount = 0;
            if (!isSpeakingNow) {
              isSpeakingNow = true;
              triggerWebcallBargeIn();
              webcallWs.send(JSON.stringify({ type: 'speech_start' }));
              setWebcallState('listening', 'Listening to you...');
            }
            webcallWs.send(pcm16.buffer);
          } else {
            if (isSpeakingNow) {
              silenceCount++;
              webcallWs.send(pcm16.buffer);
              if (silenceCount >= 8) { // ~2 seconds of silence
                isSpeakingNow = false;
                silenceCount = 0;
                setWebcallState('thinking', 'Processing question...');
                webcallWs.send(JSON.stringify({ type: 'speech_end' }));
              }
            }
          }
        };

        source.connect(webcallProcessor);
        webcallProcessor.connect(webcallAudioContext.destination);
      };

      webcallWs.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === 'ready') {
            if (data.document_loaded && webcallDocStatus) {
              webcallDocStatus.innerText = `Loaded: ${data.document_title || 'Document'}`;
            }
          } else if (data.type === 'state') {
            setWebcallState(data.state);
            if (data.state === 'interrupted') {
              stopWebcallAudioPlayback();
            }
          } else if (data.type === 'transcript') {
            appendWebcallMessage('user', data.text);
          } else if (data.type === 'answer') {
            appendWebcallMessage('assistant', data.text, data.citations);
          } else if (data.type === 'audio_chunk') {
            webcallActiveGenId = data.generation_id;
            webcallAudioQueue.push({ b64: data.audio, genId: data.generation_id });
            playNextWebcallAudio();
          }
        } catch (err) {
          console.error('WebCall ws message error:', err);
        }
      };

      webcallWs.onclose = () => {
        stopWebCall();
      };
      webcallWs.onerror = () => {
        stopWebCall();
        showToast('Web Call connection closed.', 'info');
      };
    } catch (err) {
      console.error('WebCall start error:', err);
      showToast('Could not access microphone: ' + err.message, 'error');
      setWebcallState('error', 'Microphone error: ' + err.message);
    }
  }

  function stopWebCall() {
    webcallIsCalling = false;
    stopWebcallAudioPlayback();
    if (webcallProcessor) {
      try { webcallProcessor.disconnect(); } catch (e) {}
      webcallProcessor = null;
    }
    if (webcallAudioContext) {
      try { webcallAudioContext.close(); } catch (e) {}
      webcallAudioContext = null;
    }
    if (webcallMediaStream) {
      webcallMediaStream.getTracks().forEach((t) => t.stop());
      webcallMediaStream = null;
    }
    if (webcallWs) {
      try { webcallWs.close(); } catch (e) {}
      webcallWs = null;
    }
    if (webcallStartBtn) webcallStartBtn.style.display = 'inline-flex';
    if (webcallStopBtn) webcallStopBtn.style.display = 'none';
    if (webcallMuteBtn) webcallMuteBtn.style.display = 'none';
    setWebcallState('idle', 'Call ended — Press Start Call to speak again');
  }

  if (webcallStartBtn) webcallStartBtn.addEventListener('click', startWebCall);
  if (webcallStopBtn) webcallStopBtn.addEventListener('click', stopWebCall);
  if (webcallMuteBtn) webcallMuteBtn.addEventListener('click', triggerWebcallBargeIn);

  if (webcallLangSelect) {
    webcallLangSelect.addEventListener('change', () => {
      if (webcallWs && webcallWs.readyState === WebSocket.OPEN) {
        webcallWs.send(JSON.stringify({ type: 'config', language: webcallLangSelect.value }));
      }
    });
  }

  // Sample document chips for Web Call
  document.querySelectorAll('.webcall-samples .chip').forEach((chip) => {
    chip.addEventListener('click', async () => {
      const docName = chip.dataset.sampleDoc;
      if (!docName) return;
      if (webcallDocStatus) webcallDocStatus.innerText = 'Loading ' + docName + '...';
      try {
        const res = await fetchWithAuth(`/api/documents/sample?name=${encodeURIComponent(docName)}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          if (webcallDocStatus) webcallDocStatus.innerText = `Loaded: ${data.title} (${data.pages} pages, ${data.chunks} chunks)`;
          showToast(`Loaded ${data.title}`, 'success');
          if (webcallWs && webcallWs.readyState === WebSocket.OPEN) {
            webcallWs.send(JSON.stringify({ type: 'config', sample_doc: docName }));
          }
        } else {
          if (webcallDocStatus) webcallDocStatus.innerText = 'Failed to load doc';
        }
      } catch (err) {
        if (webcallDocStatus) webcallDocStatus.innerText = 'Error loading doc: ' + err.message;
      }
    });
  });

  if (webcallUploadBtn && webcallFileInput) {
    webcallUploadBtn.addEventListener('click', () => webcallFileInput.click());
    webcallFileInput.addEventListener('change', async () => {
      if (!webcallFileInput.files || !webcallFileInput.files[0]) return;
      const file = webcallFileInput.files[0];
      if (webcallDocStatus) webcallDocStatus.innerText = `Uploading ${file.name}...`;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetchWithAuth('/api/documents/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.success) {
          if (webcallDocStatus) webcallDocStatus.innerText = `Loaded: ${data.title} (${data.pages} pages)`;
          showToast(`Uploaded ${data.title}`, 'success');
        } else {
          if (webcallDocStatus) webcallDocStatus.innerText = 'Upload failed';
        }
      } catch (err) {
        if (webcallDocStatus) webcallDocStatus.innerText = 'Upload error: ' + err.message;
      }
    });
  }

  // ==========================================
  // 13. TAB: BENCHMARK
  // ==========================================
  async function loadBenchmarkData() {
    const benchRealBody = document.getElementById('benchRealBody');
    const benchSynthBody = document.getElementById('benchSynthBody');
    if (!benchRealBody) return;

    try {
      const res = await fetchWithAuth('/api/benchmark');
      const data = await res.json();

      if (data.real_speech) {
        let html = '';
        const engines = [
          { key: 'large-v3-turbo', name: 'large-v3-turbo (Default GPU)', badge: 'Recommended' },
          { key: 'whisper-hinglish-swift', name: 'whisper-hinglish-swift', badge: 'Fastest' },
          { key: 'medium', name: 'medium', badge: 'Baseline' },
        ];

        engines.forEach((eng) => {
          const stats = data.real_speech[eng.key];
          if (!stats) return;
          const splits = stats.splits || {};
          const hiacc = splits.code_switched_hinglish ? `${splits.code_switched_hinglish.wer_pct}%` : 'N/A';
          const hi = splits.read_hindi ? `${splits.read_hindi.wer_pct}%` : 'N/A';
          const gu = splits.read_gujarati ? `${splits.read_gujarati.wer_pct}%` : 'N/A';

          html += `<tr>
            <td><strong>${eng.name}</strong> <span class="pill-badge pill-sm" style="font-size:0.7rem;">${eng.badge}</span></td>
            <td><strong>${stats.mean_wer_pct}%</strong> (raw: ${stats.mean_wer_raw_pct || stats.mean_wer_pct}%)</td>
            <td>${stats.mean_cer_pct}%</td>
            <td>${hiacc}</td>
            <td>${hi}</td>
            <td>${gu}</td>
            <td>${stats.mean_latency_ms} ms</td>
            <td>${stats.mean_rtf}x</td>
          </tr>`;
        });
        benchRealBody.innerHTML = html;
      }

      if (data.synthetic_stress && benchSynthBody) {
        let html = '';
        Object.keys(data.synthetic_stress).forEach((key) => {
          const stats = data.synthetic_stress[key];
          html += `<tr>
            <td><strong>${key}</strong></td>
            <td>${stats.wer_pct}%</td>
            <td>${stats.latency_ms} ms</td>
            <td>${stats.rtf}x</td>
          </tr>`;
        });
        benchSynthBody.innerHTML = html;
      }
    } catch (err) {
      if (benchRealBody) {
        benchRealBody.innerHTML = `<tr><td colspan="8" style="color:var(--accent-red);">Failed to load benchmark data: ${escapeHtml(err.message)}</td></tr>`;
      }
    }
  }

  // ==========================================
  // 14. TAB: HISTORY
  // ==========================================
  const historyList = document.getElementById('historyList');
  const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');
  let currentHistoryFilter = 'all';

  function renderHistoryTab() {
    if (!historyList) return;
    const filtered = dictationHistory.filter((item) => {
      if (currentHistoryFilter === 'all') return true;
      return item.type === currentHistoryFilter;
    });

    if (filtered.length === 0) {
      historyList.innerHTML = `<div class="history-empty-state">
        <div class="empty-icon">📭</div>
        <h3>No ${currentHistoryFilter === 'all' ? '' : currentHistoryFilter + ' '}history yet</h3>
        <p>Use dictation, ask document questions, or run voice commands to record activity.</p>
      </div>`;
      return;
    }

    let html = '';
    filtered.forEach((item, idx) => {
      const typeLabel = item.type === 'dictation' ? 'Dictation' : (item.type === 'qa' ? 'Doc Q&A' : 'Command');
      html += `<div class="history-item">
        <div class="history-item-header">
          <span class="history-item-type">${typeLabel}</span>
          <span class="history-item-time">${escapeHtml(item.time || '')}</span>
        </div>
        <div class="history-item-text">${escapeHtml(item.text)}</div>
        <div class="history-item-actions">
          <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText('${escapeHtml(item.text.replace(/'/g, "\\'"))}');">📋 Copy</button>
        </div>
      </div>`;
    });
    historyList.innerHTML = html;
  }

  document.querySelectorAll('[data-history-filter]').forEach((chip) => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('[data-history-filter]').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      currentHistoryFilter = chip.dataset.historyFilter;
      renderHistoryTab();
    });
  });

  if (clearAllHistoryBtn) {
    clearAllHistoryBtn.addEventListener('click', () => {
      dictationHistory = [];
      try { localStorage.removeItem('bolsamajh_dictation_history'); } catch (e) {}
      renderHistoryTab();
      renderDictateHistoryFeed();
      showToast('Session history cleared', 'info');
    });
  }

  // ==========================================
  // 15. TAB: SETTINGS
  // ==========================================
  const settingsScript = document.getElementById('settingsScript');
  const settingsHeadphone = document.getElementById('settingsHeadphone');
  const settingsHkDictation = document.getElementById('settingsHkDictation');
  const settingsHkCommand = document.getElementById('settingsHkCommand');
  const settingsHkDocQa = document.getElementById('settingsHkDocQa');
  const settingsHkDocLoad = document.getElementById('settingsHkDocLoad');
  const settingsStt = document.getElementById('settingsStt');
  const settingsDevice = document.getElementById('settingsDevice');
  const settingsLlm = document.getElementById('settingsLlm');
  const settingsTts = document.getElementById('settingsTts');
  const settingsLlmPrivacy = document.getElementById('settingsLlmPrivacy');
  const settingsTtsPrivacy = document.getElementById('settingsTtsPrivacy');
  const settingsPrivacyText = document.getElementById('settingsPrivacyText');
  const settingsPrivacyBanner = document.getElementById('settingsPrivacyBanner');

  async function loadSettingsTab(data) {
    if (!data) return;
    if (settingsScript) settingsScript.value = data.script || 'natural';
    if (settingsHkDictation && data.hotkeys) settingsHkDictation.innerText = data.hotkeys.dictation || 'Alt+Shift+Space';
    if (settingsHkCommand && data.hotkeys) settingsHkCommand.innerText = data.hotkeys.voice_command || 'Alt+Shift+C';
    if (settingsHkDocQa && data.hotkeys) settingsHkDocQa.innerText = data.hotkeys.doc_qa || 'Alt+Shift+A';
    if (settingsHkDocLoad && data.hotkeys) settingsHkDocLoad.innerText = data.hotkeys.doc_load || 'Alt+Shift+D';
    if (settingsStt) settingsStt.innerText = data.stt || 'Faster-Whisper';
    if (settingsDevice) settingsDevice.innerText = data.device || 'CUDA GPU';
    if (settingsLlm) settingsLlm.innerText = data.llm || 'Ollama Local';
    if (settingsTts) settingsTts.innerText = data.tts || 'Edge-TTS';

    const isLlmLocal = (data.llm || '').toLowerCase().includes('ollama');
    const isTtsLocal = (data.tts || '').toLowerCase().includes('piper');

    if (settingsLlmPrivacy) {
      settingsLlmPrivacy.className = isLlmLocal ? 'badge-local' : 'badge-cloud';
      settingsLlmPrivacy.innerText = isLlmLocal ? '🟢 Local (on-device)' : '🟡 Cloud API';
    }
    if (settingsTtsPrivacy) {
      settingsTtsPrivacy.className = isTtsLocal ? 'badge-local' : 'badge-cloud';
      settingsTtsPrivacy.innerText = isTtsLocal ? '🟢 Local (Piper ONNX)' : '🟡 Cloud (Edge-TTS)';
    }

    if (settingsPrivacyBanner && settingsPrivacyText) {
      if (isLlmLocal && isTtsLocal) {
        settingsPrivacyBanner.className = 'privacy-banner privacy-airgapped';
        settingsPrivacyText.innerText = '100% Offline Air-Gapped Mode: All voice, language, and vector processing is entirely local.';
      } else {
        settingsPrivacyBanner.className = 'privacy-banner privacy-hybrid';
        settingsPrivacyText.innerText = 'Hybrid Privacy Mode: STT and vector embeddings run 100% locally on-device. Voice synthesis uses Edge-TTS endpoint.';
      }
    }
  }

  if (settingsScript) {
    settingsScript.addEventListener('change', async () => {
      try {
        await fetchWithAuth('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ script: settingsScript.value }),
        });
        showToast(`Script switched to ${settingsScript.value}`, 'success');
      } catch (e) {
        showToast('Failed to update script setting', 'error');
      }
    });
  }

  if (settingsHeadphone) {
    settingsHeadphone.addEventListener('change', async () => {
      try {
        await fetchWithAuth('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ headphone_mode: settingsHeadphone.checked }),
        });
        showToast(`Headphone mode ${settingsHeadphone.checked ? 'enabled' : 'disabled'}`, 'info');
      } catch (e) {
        showToast('Failed to update headphone setting', 'error');
      }
    });
  }

  loadBenchmarkData();
  renderHistoryTab();
  loadSystemStatus().then(() => {
    fetchWithAuth('/api/status').then(r => r.json()).then(data => loadSettingsTab(data)).catch(() => {});
  });
  checkOverlayStatus();

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    }[m]));
  }
});
