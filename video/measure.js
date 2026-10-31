const fs = require('fs');
const cp = require('child_process');
const path = require('path');

const dir = path.join(__dirname, 'public', 'audio', 'calibrated');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.mp3'));

for (const file of files) {
  const fullPath = path.join(dir, file);
  const out = cp.execSync(`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${fullPath}"`).toString().trim();
  const sec = parseFloat(out);
  const frames = Math.ceil(sec * 30);
  console.log(`${file}: ${sec.toFixed(2)}s (${frames} frames)`);
}

