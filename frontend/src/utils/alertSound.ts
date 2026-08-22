let audioCtx: AudioContext | null = null;
let isMuted = false;

export function toggleAlertMute(): boolean {
  isMuted = !isMuted;
  return isMuted;
}

export function playAlertSound(severity: "info" | "warning" | "critical" = "warning"): void {
  if (isMuted) return;

  try {
    if (!audioCtx) {
      audioCtx = new AudioContext();
    }
    
    // Create a softer, sci-fi HUD chime using two oscillators (slight detune for richness)
    const osc1 = audioCtx.createOscillator();
    const osc2 = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    osc1.connect(gainNode);
    osc2.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    const freqMap = { info: 587.33, warning: 659.25, critical: 880 }; // D5, E5, A5
    const baseFreq = freqMap[severity];
    
    osc1.type = severity === "critical" ? "sawtooth" : "sine";
    osc2.type = "sine";
    
    osc1.frequency.setValueAtTime(baseFreq, audioCtx.currentTime);
    osc2.frequency.setValueAtTime(baseFreq * 1.01, audioCtx.currentTime); // Slight detune

    // ADSR Envelope
    const duration = severity === "critical" ? 0.6 : 0.3;
    gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.15, audioCtx.currentTime + 0.05); // Attack
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration); // Decay

    osc1.start(audioCtx.currentTime);
    osc2.start(audioCtx.currentTime);
    osc1.stop(audioCtx.currentTime + duration);
    osc2.stop(audioCtx.currentTime + duration);
  } catch {
    // Audio not available — silently ignore
  }
}
