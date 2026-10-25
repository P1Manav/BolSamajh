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

  const chatFeed = document.getElementById('chatFeed');
  const textQueryInput = document.getElementById('textQueryInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  const visualizerCanvas = document.getElementById('audioVisualizer');
  const latencyPill = document.getElementById('latencyPill');

  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let audioCtx = null;
  let analyser = null;
  let animFrameId = null;

  // 1. Check Initial Server Status
  fetch('/api/status')
    .then(r => r.json())
    .then(data => {
      if (data.document_loaded) {
        setDocLoaded(data.document_title, 'Indexed in memory');
      }
    })
    .catch(() => {});

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
      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      setDocLoaded(data.title, `${data.pages} pages • ${data.chunks} indexed chunks`);
      addSystemMessage(`📄 Loaded "${data.title}" successfully (${data.chunks} chunks indexed). You can now ask questions!`);
    } catch (err) {
      alert(`Error loading document: ${err.message}`);
      resetDoc();
    }
  }

  loadUrlBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) return;
    setLoadingStatus('Fetching URL...');

    try {
      const res = await fetch('/api/documents/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch URL');

      setDocLoaded(data.title, `${data.chunks} indexed chunks from web page`);
      addSystemMessage(`🌐 Loaded web page "${data.title}" (${data.chunks} chunks). Ask anything!`);
      urlInput.value = '';
    } catch (err) {
      alert(`Error loading URL: ${err.message}`);
      resetDoc();
    }
  });

  clearDocBtn.addEventListener('click', resetDoc);

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

  // 3. Question & Answer Workflow
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
    setLoadingStatus('Thinking & searching citations…');

    const assistantRow = addAssistantLoadingMessage();

    try {
      const res = await fetch('/api/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          language: langSelect.value,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to get answer');

      updateAssistantMessage(assistantRow, data);
      setLoadingStatus(`Answered in ${data.elapsed_sec}s`);
    } catch (err) {
      assistantRow.querySelector('.message-bubble').innerText = `⚠️ Error: ${err.message}`;
      setLoadingStatus('Error');
    }
  }

  // 4. Voice Recording via Browser Mic
  micBtn.addEventListener('click', toggleRecording);

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
      alert(`Mic access denied: ${err.message}`);
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
    const assistantRow = addAssistantLoadingMessage();

    try {
      const res = await fetch('/api/qa/voice', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Voice processing failed');

      // Update user message to show transcribed question text
      const userRows = document.querySelectorAll('.message-row.user');
      if (userRows.length) {
        userRows[userRows.length - 1].querySelector('.message-bubble').innerText = `🎤 "${data.question}"`;
      }

      updateAssistantMessage(assistantRow, data);
      setLoadingStatus(`Voice response in ${data.elapsed_sec}s`);
    } catch (err) {
      assistantRow.querySelector('.message-bubble').innerText = `⚠️ ${err.message}`;
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
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: commandInputText.value,
          command,
        }),
      });
      const data = await res.json();
      commandOutput.innerText = data.result;
    } catch (err) {
      commandOutput.innerText = `Error: ${err.message}`;
    }
  }

  // Helper UI functions
  function addUserMessage(text) {
    // Hide welcome card if present
    const wc = document.querySelector('.welcome-card');
    if (wc) wc.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function addAssistantLoadingMessage() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `<div class="message-bubble">⏳ Generating answer...</div>`;
    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
    return row;
  }

  function updateAssistantMessage(row, data) {
    const bubble = row.querySelector('.message-bubble');
    bubble.innerText = data.answer;

    // Citations
    if (data.citations && data.citations.length) {
      const citContainer = document.createElement('div');
      citContainer.className = 'citations-container';
      data.citations.forEach(c => {
        const pill = document.createElement('span');
        pill.className = 'citation-pill';
        pill.innerText = `📌 ${c.citation} (${Math.round(c.score * 100)}%)`;
        pill.title = c.text;
        citContainer.appendChild(pill);
      });
      row.appendChild(citContainer);
    }

    // Audio Playback
    if (data.audio_url) {
      const audioRow = document.createElement('div');
      audioRow.className = 'audio-player-row';
      const audio = document.createElement('audio');
      audio.controls = true;
      audio.autoplay = true;
      audio.src = data.audio_url;
      audioRow.appendChild(audio);
      row.appendChild(audioRow);
    }

    chatFeed.scrollTop = chatFeed.scrollHeight;
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

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});
