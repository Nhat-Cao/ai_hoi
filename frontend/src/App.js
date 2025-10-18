import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom when messages change
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        message: input
      });

      const botMessage = { 
        text: response.data.message || "I don't understand. Could you rephrase that?", 
        sender: 'bot' 
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = { 
        text: 'Sorry, I encountered an error. Please try again.', 
        sender: 'bot' 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 py-3">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-xl font-semibold text-gray-800">AI Hỏi 🍕</h1>
        </div>
      </header>

      {/* Main chat area */}
      <main className="flex-1 overflow-hidden relative">
        <div 
          ref={chatContainerRef}
          className="h-full overflow-y-auto pb-32"
        >
          <ChatWindow messages={messages} />
        </div>
        
        {/* Input area */}
        <ChatInput 
          input={input} 
          setInput={setInput} 
          sendMessage={sendMessage} 
        />
      </main>
    </div>
  );
}

export default App;