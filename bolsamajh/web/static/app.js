// BolSamajh Web Client Logic

document.addEventListener('DOMContentLoaded', () => {
  // Elements
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

  const commandInputText = document.getElementById('commandInputText');
  const runCommandBtn = document.getElementById('runCommandBtn');
  const commandOutput = document.getElementById('commandOutput');
  const commandShortcutBadge = document.getElementById('commandShortcutBadge');

  const chatFeed = document.getElementById('chatFeed');
  const textQueryInput = document.getElementById('textQueryInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const visualizerCanvas = document.getElementById('audioVisualizer');
  const latencyPill = document.getElementById('latencyPill');

  // In-memory state
  let currentApiKey = '';
  let chatHistory = [];

  const apiKeyContainer = document.getElementById('apiKeyContainer');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const setApiKeyBtn = document.getElementById('setApiKeyBtn');
  const apiKeyBadge = document.getElementById('apiKeyBadge');
  const authAlertBanner = document.getElementById('authAlertBanner');
  const authAlertText = document.getElementById('authAlertText');
  const dismissAuthAlertBtn = document.getElementById('dismissAuthAlertBtn');

  // Inline Toast Notification helper
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
    }, 4000);
  }

  function setApiKey(key) {
    currentApiKey = (key || '').trim();
    if (currentApiKey) {
      if (apiKeyBadge) apiKeyBadge.style.display = 'inline-block';
      if (apiKeyContainer) apiKeyContainer.classList.remove('auth-error');
      hideAuthError();
      showToast('API Key configured in memory.', 'success');
    } else {
      if (apiKeyBadge) apiKeyBadge.style.display = 'none';
    }
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
    if (apiKeyContainer) {
      apiKeyContainer.classList.add('auth-error');
    }
    if (apiKeyInput) {
      apiKeyInput.focus();
    }
  }

  function hideAuthError() {
    if (authAlertBanner) authAlertBanner.style.display = 'none';
    if (apiKeyContainer) apiKeyContainer.classList.remove('auth-error');
  }

  async function fetchWithAuth(url, options = {}) {
    options = Object.assign({}, options);
    const headers = options.headers
      ? (options.headers instanceof Headers ? options.headers : Object.assign({}, options.headers))
      : {};
    if (currentApiKey) {
      if (headers instanceof Headers) {
        headers.set('Authorization', `Bearer ${currentApiKey}`);
      } else {
        headers['Authorization'] = `Bearer ${currentApiKey}`;
      }
    }
    options.headers = headers;

    const res = await fetch(url, options);
    if (res.status === 401) {
      showAuthError('⚠️ Authentication required (HTTP 401 Unauthorized). Please set your BOLSAMAJH_API_KEY in the top bar.');
    }
    return res;
  }

  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let audioCtx = null;
  let analyser = null;
  let animFrameId = null;

  // 1. Check Initial Server Status & Sync Configured Hotkeys
  fetchWithAuth('/api/status')
    .then(r => r.json())
    .then(data => {
      const statusEl = document.getElementById('sttStatusText');
      if (statusEl && data.device) {
        statusEl.textContent = `${data.device} • ${data.stt} • ${data.tts}`;
      }
      if (data.hotkeys && data.hotkeys.voice_command && commandShortcutBadge) {
        commandShortcutBadge.innerText = data.hotkeys.voice_command.toUpperCase();
      }
      if (data.document_loaded) {
        setDocLoaded('Active Document', 'Indexed in memory for current session');
      }
    })
    .catch(() => {
      const statusEl = document.getElementById('sttStatusText');
      if (statusEl) statusEl.textContent = 'Server connecting...';
    });

  // 2. Document Upload Handlers
  browseBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) uploadFile(e.target.files[0]);
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
  });

  async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    setLoadingStatus('Uploading & indexing document...');

    try {
      const res = await fetchWithAuth('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      setDocLoaded(data.title, `${data.pages} pages • ${data.chunks} indexed chunks`);
      addSystemMessage(`📄 Loaded "${data.title}" successfully (${data.chunks} chunks indexed). You can now ask questions!`);
      showToast(`Loaded ${data.title} (${data.chunks} chunks)`, 'success');
    } catch (err) {
      showToast(`Error loading document: ${err.message}`, 'error');
      resetDoc();
    }
  }

  loadUrlBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) return;
    setLoadingStatus('Fetching URL...');

    try {
      const res = await fetchWithAuth('/api/documents/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch URL');

      setDocLoaded(data.title, `${data.chunks} indexed chunks from web page`);
      addSystemMessage(`🌐 Loaded web page "${data.title}" (${data.chunks} chunks). Ask anything!`);
      showToast(`Loaded web page: ${data.title}`, 'success');
      urlInput.value = '';
    } catch (err) {
      showToast(`Error loading URL: ${err.message}`, 'error');
      resetDoc();
    }
  });

  // Clear Document Handler with session DELETE API call
  clearDocBtn.addEventListener('click', async () => {
    try {
      await fetchWithAuth('/api/document', { method: 'DELETE' });
      resetDoc();
      showToast('Document cleared from session memory.', 'info');
      addSystemMessage('Document has been cleared.');
    } catch (err) {
      resetDoc();
    }
  });

  // Clear Chat History Handler
  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', () => {
      chatHistory = [];
      const rows = chatFeed.querySelectorAll('.message-row');
      rows.forEach(r => r.remove());
      const wc = document.querySelector('.welcome-card');
      if (wc) wc.style.display = 'block';
      clearHistoryBtn.style.display = 'none';
      showToast('Chat history cleared.', 'info');
    });
  }

  function setDocLoaded(title, meta) {
    dropzone.style.display = 'none';
    docInfoCard.style.display = 'flex';
    docTitle.innerText = title;
    docMeta.innerText = meta;
    docBadge.innerText = 'Active';
    docBadge.classList.add('active');
    latencyPill.innerText = 'Doc Ready';
  }

  function resetDoc() {
    dropzone.style.display = 'block';
    docInfoCard.style.display = 'none';
    docBadge.innerText = 'No doc loaded';
    docBadge.classList.remove('active');
    latencyPill.innerText = 'Ready';
  }

  function setLoadingStatus(text) {
    latencyPill.innerText = text;
  }

  // 3. Question & Answer Workflow with SSE Token-by-Token Streaming
  sendBtn.addEventListener('click', () => {
    const q = textQueryInput.value.trim();
    if (q) handleTextQuery(q);
  });

  textQueryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = textQueryInput.value.trim();
      if (q) handleTextQuery(q);
    }
  });

  // Sample Question Chips
  document.querySelectorAll('.sample-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-q');
      handleTextQuery(q);
    });
  });

  async function handleTextQuery(question) {
    addUserMessage(question);
    textQueryInput.value = '';
    setLoadingStatus('Streaming answer…');
    if (clearHistoryBtn) clearHistoryBtn.style.display = 'inline-block';

    const assistantRow = addAssistantLoadingMessage();
    const bubble = assistantRow.querySelector('.message-bubble');

    let fullText = '';
    const encodedQ = encodeURIComponent(question);
    const encodedLang = encodeURIComponent(langSelect.value);

    try {
      const res = await fetchWithAuth(`/api/qa/stream?question=${encodedQ}&language=${encodedLang}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep incomplete trailing fragment

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
            if (dataObj.error) {
              showToast(`Streaming error: ${dataObj.error}`, 'error');
            }
          } catch (e) {
            // Ignore non-json SSE frames
          }
        }
      }

      setLoadingStatus('Answer complete');
      chatHistory.push({ role: 'user', content: question });
      chatHistory.push({ role: 'assistant', content: fullText });

    } catch (err) {
      bubble.innerText = `⚠️ Error: ${err.message}`;
      showToast(`Q&A Error: ${err.message}`, 'error');
      setLoadingStatus('Error');
    }
  }

  // 4. Voice Recording via Browser Mic (Click-to-Toggle and Hold-to-Talk)
  let micPressStartTime = 0;
  let isHoldRecording = false;

  micBtn.addEventListener('click', () => {
    // If not a hold-to-talk release, toggle normally
    if (!isHoldRecording) {
      toggleRecording();
    }
    isHoldRecording = false;
  });

  micBtn.addEventListener('mousedown', () => {
    micPressStartTime = Date.now();
  });

  micBtn.addEventListener('mouseup', () => {
    const pressDuration = Date.now() - micPressStartTime;
    // If user held for > 400ms while recording was active, treat as hold-to-talk release
    if (isRecording && pressDuration > 400) {
      isHoldRecording = true;
      stopRecording();
    }
  });

  async function toggleRecording() {
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = handleVoiceRecorded;
      mediaRecorder.start();
      isRecording = true;

      micBtn.classList.add('recording');
      visualizerCanvas.style.display = 'block';
      setupVisualizer(stream);
      setLoadingStatus('Listening to your voice…');
    } catch (err) {
      showToast(`Mic access denied: ${err.message}`, 'error');
    }
  }

  function stopRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      isRecording = false;
      micBtn.classList.remove('recording');
      visualizerCanvas.style.display = 'none';
      if (animFrameId) cancelAnimationFrame(animFrameId);
      setLoadingStatus('Transcribing speech with Whisper…');
    }
  }

  async function handleVoiceRecorded() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('language', langSelect.value);

    addUserMessage('🎤 Voice question submitted...');
    if (clearHistoryBtn) clearHistoryBtn.style.display = 'inline-block';
    const assistantRow = addAssistantLoadingMessage();

    try {
      const res = await fetchWithAuth('/api/qa/voice', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Voice processing failed');

      // Update user message with transcribed question text
      const userRows = document.querySelectorAll('.message-row.user');
      if (userRows.length) {
        userRows[userRows.length - 1].querySelector('.message-bubble').innerText = `🎤 "${data.question}"`;
      }

      updateAssistantMessage(assistantRow, data);
      setLoadingStatus(`Voice response in ${data.elapsed_sec}s`);
      chatHistory.push({ role: 'user', content: data.question });
      chatHistory.push({ role: 'assistant', content: data.answer });
    } catch (err) {
      assistantRow.querySelector('.message-bubble').innerText = `⚠️ ${err.message}`;
      showToast(`Voice QA Error: ${err.message}`, 'error');
      setLoadingStatus('Error');
    }
  }

  // Audio Canvas Visualizer
  function setupVisualizer(stream) {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);

    const canvas = visualizerCanvas;
    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      animFrameId = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = (canvas.width / bufferLength) * 2;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillStyle = `rgb(${dataArray[i] + 50}, 102, 241)`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
        x += barWidth;
      }
    }
    draw();
  }

  // 5. In-App Commands Playground
  document.querySelectorAll('.command-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const cmd = chip.getAttribute('data-cmd');
      executeCommand(cmd);
    });
  });

  runCommandBtn.addEventListener('click', () => {
    executeCommand('Improve clarity and flow');
  });

  async function executeCommand(command) {
    const text = commandInputText.value.trim();
    if (!text) {
      commandInputText.value = "Hey team, just wanted to ping that the deployment might happen tomorrow or maybe day after, let's see how things go.";
    }

    commandOutput.style.display = 'block';
    commandOutput.innerText = '⚡ Processing command with LLM…';

    try {
      const res = await fetchWithAuth('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: commandInputText.value,
          command,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Command failed');
      commandOutput.innerText = data.result;
    } catch (err) {
      commandOutput.innerText = `Error: ${err.message}`;
      showToast(`Command error: ${err.message}`, 'error');
    }
  }

  // Helper UI functions
  function addUserMessage(text) {
    const wc = document.querySelector('.welcome-card');
    if (wc) wc.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row user';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerText = text;
    row.appendChild(bubble);
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function addAssistantLoadingMessage() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerText = '⏳ Generating answer...';
    row.appendChild(bubble);
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
    return row;
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

    citations.forEach(c => {
      const pill = document.createElement('span');
      pill.className = 'citation-pill';
      const pct = c.score ? ` (${Math.round(c.score * 100)}%)` : '';
      pill.innerText = `📌 ${c.citation}${pct}`;
      if (c.text) pill.title = c.text;
      citContainer.appendChild(pill);
    });
  }

  function updateAssistantMessage(row, data) {
    const bubble = row.querySelector('.message-bubble');
    bubble.innerText = data.answer;

    if (data.citations && data.citations.length) {
      renderCitations(row, data.citations);
    }

    // Audio Playback
    if (data.audio_url) {
      const audioRow = document.createElement('div');
      audioRow.className = 'audio-player-row';
      const audio = document.createElement('audio');
      audio.controls = true;
      audioRow.appendChild(audio);
      row.appendChild(audioRow);

      fetchWithAuth(data.audio_url)
        .then(async (r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const blob = await r.blob();
          const blobUrl = URL.createObjectURL(blob);
          audio.src = blobUrl;
          audio.autoplay = true;
          audio.play().catch(() => {});
        })
        .catch((err) => {
          const errSpan = document.createElement('span');
          errSpan.className = 'audio-err-msg';
          errSpan.innerText = `🔊 Audio unavailable (${err.message})`;
          audioRow.appendChild(errSpan);
        });
    }

    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function addSystemMessage(text) {
    const wc = document.querySelector('.welcome-card');
    if (wc) wc.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row assistant';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.style.borderLeft = '3px solid var(--accent-cyan)';
    bubble.innerText = text;
    row.appendChild(bubble);
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }
});
