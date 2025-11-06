import React, { useState, useRef } from 'react';
import { DEFAULT_BACKEND } from '@/service/api';

interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscription }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      console.log('🎤 Requesting microphone access...');
      
      // Check if mediaDevices is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support audio recording. Please use a modern browser like Chrome, Firefox, or Edge.');
      }

      // List available audio input devices
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices.filter(device => device.kind === 'audioinput');
      console.log('🎙️ Available microphones:', audioInputs.map(d => ({
        label: d.label || 'Unknown device',
        deviceId: d.deviceId
      })));

      // Request ONLY microphone audio, not desktop/tab audio
      // Use default microphone (user can select in browser settings)
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1, // Mono for better speech recognition
          sampleRate: 48000, // Higher quality
          sampleSize: 16
        },
        video: false  // Explicitly no video
      });
      
      console.log('✅ Microphone access granted');
      const audioTrack = stream.getAudioTracks()[0];
      console.log('🎙️ Using microphone:', audioTrack.label);
      console.log('🎙️ Audio settings:', audioTrack.getSettings());
      
      // Test audio levels
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);
      analyser.fftSize = 256;
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      
      // Check audio level once
      setTimeout(() => {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        console.log('📊 Audio level test:', average.toFixed(2), '(should be > 0 when speaking)');
        if (average < 1) {
          console.warn('⚠️ WARNING: Very low audio level detected. Microphone might not be working!');
        }
      }, 500);
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log('📊 Audio chunk received:', event.data.size, 'bytes');
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('🔊 Recording stopped. Total size:', audioBlob.size, 'bytes');
        console.log('📦 Audio format:', audioBlob.type);
        
        // Check blob size
        if (audioBlob.size < 1000) {
          console.error('❌ Audio blob is too small (< 1KB). Recording might have failed.');
          alert('Recording failed: Audio data is too small. Please check your microphone settings and try again.');
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        
        await sendAudioToBackend(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log('🔴 Recording started');
    } catch (error: any) {
      console.error('❌ Error accessing microphone:', error);
      if (error.name === 'NotAllowedError') {
        alert('Microphone access denied. Please allow microphone access in your browser settings.');
      } else if (error.name === 'NotFoundError') {
        alert('No microphone found. Please connect a microphone and try again.');
      } else {
        alert(`Could not access microphone: ${error.message}`);
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToBackend = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      console.log('📤 Sending audio to backend...', {
        size: audioBlob.size,
        type: audioBlob.type,
        backend: DEFAULT_BACKEND
      });
      
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await fetch(`${DEFAULT_BACKEND}/speech-to-text`, {
        method: 'POST',
        body: formData,
      });

      console.log('📥 Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('📝 Transcription result:', data);
      
      if (data.text) {
        onTranscription(data.text);
        console.log('✅ Transcription successful:', data.text);
      } else if (data.error) {
        console.error('❌ Transcription error:', data.error);
        alert(`Failed to transcribe audio: ${data.error}`);
      } else {
        console.warn('⚠️ Empty transcription received');
        alert('No speech detected. Please try again and speak clearly.');
      }
    } catch (error: any) {
      console.error('❌ Error sending audio:', error);
      alert(`Failed to process audio: ${error.message}\n\nMake sure the backend is running on ${DEFAULT_BACKEND}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <button
      type="button"
      onClick={isRecording ? stopRecording : startRecording}
      disabled={isProcessing}
      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
        isRecording
          ? 'bg-red-500 hover:bg-red-600 animate-pulse'
          : isProcessing
          ? 'bg-gray-600 cursor-not-allowed'
          : 'bg-orange-400 hover:bg-orange-300'
      } text-white focus:outline-none`}
      title={isRecording ? 'Stop recording' : 'Start voice input'}
    >
      {isProcessing ? (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      ) : isRecording ? (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <rect x="6" y="6" width="8" height="8" rx="1" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  );
};

export default VoiceRecorder;
