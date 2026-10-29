// BolSamajh Web Client — Wispr Flow Studio & Voice Intelligence Engine

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
  if (['dictate', 'doc', 'actions', 'mobile', 'system'].includes(hash)) {
    switchTab(hash);
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
  // 6. TAB 1: WISPR FLOW DICTATION STUDIO
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

  loadSystemStatus();

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
