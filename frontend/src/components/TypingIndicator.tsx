'use client';

import { useEffect, useState } from 'react';

export default function TypingIndicator() {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return '•';
        return prev + '•';
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <span className="inline-flex items-center text-lg">
      <span className="w-6 text-center">{dots}</span>
    </span>
  );
}