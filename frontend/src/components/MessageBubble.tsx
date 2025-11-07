import React, { useState, useRef } from 'react';
import { DEFAULT_BACKEND } from '@/service/api';
import TypingIndicator from './TypingIndicator';

interface MessageBubbleProps {
  role: 'user' | 'bot';
  text: string;
  isTyping?: boolean;
}

export default function MessageBubble({ role, text, isTyping }: MessageBubbleProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlayAudio = async () => {
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${DEFAULT_BACKEND}/text-to-speech`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
      setIsPlaying(true);
    } catch (error) {
      console.error('Error playing audio:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`my-1.5 p-3 rounded-xl max-w-[85%] shadow-md ${
      role === 'user' 
        ? 'bg-orange-400 self-end rounded-br-sm' 
        : 'bg-[#1f1f1f] self-start rounded-bl-sm border border-[#2b2b2b]'
    }`}>
      {isTyping ? (
        <TypingIndicator />
      ) : (
        <>
          <p className="text-white text-base leading-[22px] white-space-preline">{text}</p>
          {role === 'bot' && (
            <button
              onClick={handlePlayAudio}
              disabled={isLoading}
              className="mt-2 p-1.5 rounded-full bg-orange-400 hover:bg-orange-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={isPlaying ? 'Pause audio' : 'Play audio'}
            >
              {isLoading ? (
                <svg className="w-4 h-4 animate-spin text-[#0b1b33]" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : isPlaying ? (
                <svg className="w-4 h-4 text-[#0b1b33]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-[#0b1b33]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              )}
            </button>
          )}
        </>
      )}
    </div>
  );
}
