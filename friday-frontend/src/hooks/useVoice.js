import { useState, useEffect, useRef, useCallback } from 'react';

// Priority list of sweet-sounding female voices (checked in order)
const PREFERRED_VOICE_NAMES = [
  'Google UK English Female',
  'Microsoft Zira',         // Windows built-in — warm female
  'Microsoft Hazel',        // UK female
  'Microsoft Susan',
  'Samantha',               // macOS/iOS — soft, natural
  'Karen',                  // macOS Australian female
  'Victoria',               // macOS — gentle female
  'Moira',                  // macOS Irish female
  'Tessa',                  // macOS South African female
  'Fiona',                  // macOS Scottish female
  'Google US English',      // Fallback Google voice
];

function pickSweetVoice(voices) {
  // Try each preferred name first (exact or partial match)
  for (const name of PREFERRED_VOICE_NAMES) {
    const match = voices.find((v) => v.name.includes(name));
    if (match) return match;
  }
  // Then any English female voice
  const femaleKeyword = voices.find(
    (v) => v.lang.startsWith('en') && v.name.toLowerCase().includes('female')
  );
  if (femaleKeyword) return femaleKeyword;
  // Fallback: any English voice
  return voices.find((v) => v.lang.startsWith('en')) || null;
}

export function useVoice({ voiceEnabled }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const voiceRef = useRef(null);

  // Pick the sweetest available female voice
  useEffect(() => {
    const pickVoice = () => {
      const voices = synthRef.current.getVoices();
      voiceRef.current = pickSweetVoice(voices);
    };
    pickVoice();
    synthRef.current.onvoiceschanged = pickVoice;
  }, []);

  // Set up SpeechRecognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let finalTranscript = '';

    recognition.onresult = (e) => {
      let interimTranscript = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalTranscript += e.results[i][0].transcript + ' ';
        } else {
          interimTranscript += e.results[i][0].transcript;
        }
      }
      setTranscript(finalTranscript + interimTranscript);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => {
      setIsListening(false);
      finalTranscript = ''; // Reset on end
    };

    recognitionRef.current = recognition;
  }, []);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    setTranscript('');
    setIsListening(true);
    recognitionRef.current.start();
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    recognitionRef.current.stop();
    setIsListening(false);
  }, []);

  const speak = useCallback(
    (text) => {
      if (!voiceEnabled) return;
      synthRef.current.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = voiceRef.current;
      utterance.rate = 0.95;   // slightly slower = warmer, more natural
      utterance.pitch = 1.15;  // slightly higher pitch = sweeter tone
      utterance.volume = 1.0;
      synthRef.current.speak(utterance);
    },
    [voiceEnabled]
  );

  const cancelSpeech = useCallback(() => {
    synthRef.current.cancel();
  }, []);

  return { isListening, transcript, setTranscript, startListening, stopListening, speak, cancelSpeech, selectedVoice: voiceRef };
}
