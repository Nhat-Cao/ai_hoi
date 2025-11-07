/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useRef } from 'react';
import { DEFAULT_BACKEND } from '@/service/api';

interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscription }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [useBackendFallback, setUseBackendFallback] = useState(false);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    // Try Web Speech API first
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (SpeechRecognition && !useBackendFallback) {
      startWebSpeechRecognition();
    } else {
      // Fallback to MediaRecorder + Backend
      await startMediaRecorderFallback();
    }
  };

  const startWebSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'vi-VN'; // Vietnamese
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsRecording(true);
      console.log('🎤 Đang ghi âm (Web Speech API)...');
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      console.log('📝 Nhận diện được:', transcript);
      onTranscription(transcript);
    };

    recognition.onerror = (event: any) => {
      console.error('❌ Lỗi Web Speech API:', event.error);
      setIsRecording(false);
      
      if (event.error === 'not-allowed') {
        alert('Vui lòng cho phép truy cập microphone trong cài đặt trình duyệt.');
      } else if (event.error === 'no-speech') {
        alert('Không phát hiện giọng nói. Vui lòng thử lại.');
      } else {
        // Automatically switch to backend fallback
        console.log('🔄 Tự động chuyển sang backend fallback...');
        setUseBackendFallback(true);
        setTimeout(() => startMediaRecorderFallback(), 100);
      }
    };

    recognition.onend = () => {
      setIsRecording(false);
      console.log('🛑 Kết thúc ghi âm');
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const startMediaRecorderFallback = async () => {
    try {
      console.log('🎤 Sử dụng backend fallback...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
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
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Không thể truy cập microphone. Vui lòng kiểm tra quyền truy cập.');
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && !useBackendFallback) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else if (mediaRecorderRef.current && isRecording) {
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

      console.log('📤 Đang gửi audio đến backend...');
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
        console.log('✅ Backend transcription:', data.text);
        onTranscription(data.text);
        console.log('✅ Transcription successful:', data.text);
      } else if (data.error) {
        console.error('Transcription error:', data.error);
        alert('Không thể nhận diện giọng nói. Vui lòng thử lại.');
      }
    } catch (error) {
      console.error('Error sending audio:', error);
      alert('Lỗi kết nối đến server. Vui lòng thử lại.');
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
      } text-[#0b1b33] focus:outline-none`}
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
          <path d="M10 2a4 4 0 00-4 4v4a4 4 0 008 0V6a4 4 0 00-4-4zM8 6a2 2 0 114 0v4a2 2 0 11-4 0V6zM4.5 12.5A.5.5 0 015 12a5 5 0 0010 0 .5.5 0 011 0 6 6 0 01-5.5 5.975V20h3a.5.5 0 010 1h-7a.5.5 0 010-1h3v-2.025A6 6 0 014 12a.5.5 0 01.5-.5z" />
        </svg>
      )}
    </button>
  );
};

export default VoiceRecorder;
