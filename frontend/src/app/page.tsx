'use client';

import { useState, useRef, useEffect } from 'react';
import Header from '@/components/Header';
import MessageList from '@/components/MessageList';
import MessageInput from '@/components/MessageInput';
import SuggestionChips from '@/components/SuggestionChips';
import { getUserLocation, sendChatMessage } from '@/service/api';

export default function Home() {
  const [messages, setMessages] = useState<Array<{ id: string; role: 'user' | 'bot'; text: string; isTyping?: boolean }>>([{
    id: 'sys',
    role: 'bot',
    text: 'Chào bạn! Mình là trợ lý ẩm thực của bạn đây! 😊🍜\n\nBạn muốn tìm món gì ngon hôm nay? Cứ hỏi mình nhé - mình biết hết các quán ngon xung quanh đây! ✨'
  }]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<string | undefined>();
  const [showSuggestions, setShowSuggestions] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);

  const handleSuggestionSelect = (text: string) => {
    setInputText(text);
    setShowSuggestions(false);
    // Auto-send after a short delay
    setTimeout(() => {
      const event = new Event('submit');
      handleSend();
    }, 100);
  };

  const handleSend = async () => {
    if (!inputText.trim() || sending) return;

    // Hide suggestions after first message
    setShowSuggestions(false);

    const newMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      text: inputText.trim()
    };

    const typingMessage = {
      id: 'typing',
      role: 'bot' as const,
      text: '',
      isTyping: true
    };

    setMessages(prev => [...prev, newMessage]);
    setInputText('');
    setSending(true);

    try {
      setMessages(prev => [...prev, typingMessage]);
      
      // Build conversation history (exclude system message and typing indicator)
      const history = messages
        .filter(msg => msg.id !== 'sys' && msg.id !== 'typing')
        .map(msg => ({
          role: msg.role === 'user' ? 'user' : 'assistant',
          content: msg.text
        }));
      
      const data = await sendChatMessage(newMessage.text, currentLocation || "", history);
     
      
      setMessages(prev => prev.filter(msg => msg.id !== 'typing').concat({
        id: Date.now().toString(),
        role: 'bot',
        text: data.message
      }));
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    (async () => {
      const locationData = await getUserLocation();
      if (locationData?.address_details) {
        const { road, suburb, city } = locationData.address_details;
        const parts = [road, suburb, city].filter(part => part && part !== 'undefined');
        const locationStr = parts.join(', ');
        if (locationStr) {
          setCurrentLocation(locationStr);
        }
      }
    })();
  }, []);

  return (
  <main className="flex flex-col h-screen bg-[#1c1c1c]">
    <Header currentLocation={currentLocation} />

    {/* Chat area */}
    <div className="flex-1 overflow-y-auto no-scrollbar px-3 sm:px-[15%] md:px-[20%] lg:px-[25%]">
      <MessageList messages={messages} listRef={listRef}/>
      
      {/* Suggestion chips - show only at start */}
      {showSuggestions && messages.length === 1 && (
        <div className="mt-4">
          <SuggestionChips onSelect={handleSuggestionSelect} disabled={sending} />
        </div>
      )}
    </div>

    {/* Input area */}
    <div className="px-3 sm:px-[15%] md:px-[20%] lg:px-[25%]">
      <MessageInput
        value={inputText}
        onChangeText={setInputText}
        onSend={handleSend}
        sending={sending}
      />
    </div>
  </main>
);
}
