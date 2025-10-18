import React from 'react';

const ChatInput = ({ input, setInput, sendMessage }) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-white to-transparent pt-10">
      <div className="max-w-4xl mx-auto px-4 pb-6">
        <form onSubmit={sendMessage} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full p-4 pr-20 bg-white border border-gray-300 rounded-lg shadow-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 text-gray-700"
            placeholder="Type your message here..."
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInput;