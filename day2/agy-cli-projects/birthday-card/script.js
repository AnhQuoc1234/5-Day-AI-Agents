// Web Audio API Synthesizer for "Happy Birthday" Melody
class BirthdaySynth {
  constructor() {
    this.audioCtx = null;
    this.isPlaying = false;
    this.notes = [
      { note: 'G4', dur: 0.75 }, { note: 'G4', dur: 0.25 }, { note: 'A4', dur: 1 }, { note: 'G4', dur: 1 }, { note: 'C5', dur: 1 }, { note: 'B4', dur: 2 },
      { note: 'G4', dur: 0.75 }, { note: 'G4', dur: 0.25 }, { note: 'A4', dur: 1 }, { note: 'G4', dur: 1 }, { note: 'D5', dur: 1 }, { note: 'C5', dur: 2 },
      { note: 'G4', dur: 0.75 }, { note: 'G4', dur: 0.25 }, { note: 'G5', dur: 1 }, { note: 'E5', dur: 1 }, { note: 'C5', dur: 1 }, { note: 'B4', dur: 1 }, { note: 'A4', dur: 2 },
      { note: 'F5', dur: 0.75 }, { note: 'F5', dur: 0.25 }, { note: 'E5', dur: 1 }, { note: 'C5', dur: 1 }, { note: 'D5', dur: 1 }, { note: 'C5', dur: 2 }
    ];
    this.frequencies = {
      'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25,
      'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99
    };
    this.currentTimeout = null;
  }

  init() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
  }

  playNote(freq, start, duration) {
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = 'triangle'; // Warm, vintage synth sound
    osc.frequency.setValueAtTime(freq, start);

    // Apply envelope (attack, decay, sustain, release)
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(0.3, start + 0.05); // Attack
    gain.gain.exponentialRampToValueAtTime(0.15, start + duration * 0.5); // Decay/Sustain
    gain.gain.exponentialRampToValueAtTime(0.001, start + duration); // Release

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);

    osc.start(start);
    osc.stop(start + duration);
  }

  playMelody() {
    this.init();
    if (this.isPlaying) return;
    this.isPlaying = true;

    let time = this.audioCtx.currentTime;
    const tempo = 0.55; // Seconds per beat

    const playNext = (index) => {
      if (!this.isPlaying || index >= this.notes.length) {
        this.isPlaying = false;
        const audioBtn = document.querySelector('.btn-audio');
        if (audioBtn) audioBtn.classList.remove('is-playing');
        // Restart or loop if needed. Here we just stop.
        return;
      }

      const noteObj = this.notes[index];
      const freq = this.frequencies[noteObj.note];
      const dur = noteObj.dur * tempo;

      if (freq) {
        this.playNote(freq, this.audioCtx.currentTime, dur - 0.05);
      }

      this.currentTimeout = setTimeout(() => {
        playNext(index + 1);
      }, dur * 1000);
    };

    playNext(0);
  }

  stop() {
    this.isPlaying = false;
    if (this.currentTimeout) {
      clearTimeout(this.currentTimeout);
    }
  }
}

// Initializing the audio class
const synth = new BirthdaySynth();

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
  const card = document.getElementById('birthday-card');
  const audioBtn = document.getElementById('audio-toggle');
  const audioIconOn = document.getElementById('audio-icon-on');
  const audioIconOff = document.getElementById('audio-icon-off');
  
  // Customizing elements
  const inputName = document.getElementById('input-name');
  const inputWishes = document.getElementById('input-wishes');
  const dispName = document.getElementById('recipient-display');
  const dispWishes = document.getElementById('wishes-display');

  // Interactive candles
  const candles = document.querySelectorAll('.candle');

  let firstOpen = true;

  // Flip card handler
  card.addEventListener('click', (e) => {
    // Avoid flipping the card when interacting with input panels or audio button
    if (e.target.closest('.candle') || e.target.closest('.customize-panel') || e.target.closest('.audio-control')) {
      return;
    }

    card.classList.toggle('is-open');

    // Trigger audio and confetti on first open
    if (card.classList.contains('is-open')) {
      if (firstOpen) {
        triggerConfettiCascade();
        firstOpen = false;
        // Start the music after a small delay
        setTimeout(() => {
          startMusic();
        }, 600);
      } else {
        triggerConfettiBurst();
      }
    } else {
      // Stop the music if card is closed
      stopMusic();
    }
  });

  // Audio Toggle Button
  audioBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (synth.isPlaying) {
      stopMusic();
    } else {
      startMusic();
    }
  });

  function startMusic() {
    synth.playMelody();
    audioIconOn.style.display = 'block';
    audioIconOff.style.display = 'none';
    audioBtn.classList.add('is-playing');
  }

  function stopMusic() {
    synth.stop();
    audioIconOn.style.display = 'none';
    audioIconOff.style.display = 'block';
    audioBtn.classList.remove('is-playing');
  }

  // Personalization updates
  inputName.addEventListener('input', (e) => {
    dispName.textContent = e.target.value || 'Someone Special';
  });

  inputWishes.addEventListener('input', (e) => {
    dispWishes.textContent = e.target.value || 'Wishing you a day filled with love, laughter, and all your heart desires. May this year ahead bring you endless joy and beautiful memories!';
  });

  // Candle interactions
  candles.forEach(candle => {
    candle.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!candle.classList.contains('blown')) {
        candle.classList.add('blown');
        triggerConfettiBurst();
        
        // Play brief bubble sound using Synth
        playCandleBlowSound();

        // Check if all candles are blown
        const allBlown = Array.from(candles).every(c => c.classList.contains('blown'));
        if (allBlown) {
          setTimeout(() => {
            triggerMegaConfetti();
          }, 500);
        }
      }
    });
  });

  function playCandleBlowSound() {
    synth.init();
    if (synth.audioCtx) {
      const time = synth.audioCtx.currentTime;
      // High frequency descending sweep simulating blowing wind/spark
      const osc = synth.audioCtx.createOscillator();
      const gain = synth.audioCtx.createGain();
      osc.frequency.setValueAtTime(800, time);
      osc.frequency.exponentialRampToValueAtTime(100, time + 0.3);
      gain.gain.setValueAtTime(0.1, time);
      gain.gain.exponentialRampToValueAtTime(0.001, time + 0.3);
      osc.connect(gain);
      gain.connect(synth.audioCtx.destination);
      osc.start(time);
      osc.stop(time + 0.3);
    }
  }

  // Confetti effects (utilizes canvas-confetti library)
  function triggerConfettiBurst() {
    if (typeof confetti === 'function') {
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 },
        colors: ['#a855f7', '#6366f1', '#ec4899', '#f5af19', '#3b82f6']
      });
    }
  }

  function triggerConfettiCascade() {
    if (typeof confetti === 'function') {
      const duration = 2.5 * 1000;
      const end = Date.now() + duration;

      (function frame() {
        confetti({
          particleCount: 3,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: ['#a855f7', '#6366f1', '#ec4899', '#f5af19']
        });
        confetti({
          particleCount: 3,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: ['#a855f7', '#6366f1', '#ec4899', '#f5af19']
        });

        if (Date.now() < end) {
          requestAnimationFrame(frame);
        }
      }());
    }
  }

  function triggerMegaConfetti() {
    if (typeof confetti === 'function') {
      // Firework effect
      const duration = 5 * 1000;
      const animationEnd = Date.now() + duration;
      const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 100 };

      function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
      }

      const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
          return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);
        // since particles fall down, animate a bit higher than they would
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
      }, 250);
    }
  }
});
