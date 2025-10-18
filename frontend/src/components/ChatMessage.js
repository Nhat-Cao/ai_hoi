import React from 'react';

const ChatMessage = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className="flex w-full max-w-4xl">
        <div className={`flex gap-4 p-6 w-full ${!isUser ? 'bg-gray-50' : ''}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-blue-500' : 'bg-green-500'
          }`}>
            {isUser ? '👤' : '🤖'}
          </div>
          <div className="flex-grow">
            <div className={`text-base ${isUser ? 'text-gray-800' : 'text-gray-700'}`}>
              {message.text}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;