import React from 'react';

const ChatInput = ({ input, setInput, sendMessage }) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-white to-transparent pt-10">
      <div className="max-w-4xl mx-auto px-4 pb-6">
        <form onSubmit={sendMessage} className="relative">
            <div className="relative flex items-end w-full p-4 bg-gray-50 border-t">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                    rows={1}
                    className="
                    w-full p-4 pr-14 bg-white border border-gray-300
                    rounded-3xl shadow-md text-gray-700 resize-none
                    focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200
                    min-h-[48px] max-h-[40vh] no-scrollbar
                    "
                    style={{
                    overflowY: 'auto',
                    height: 'auto',
                    }}
                    onInput={(e) => {
                    const el = e.target;
                    el.style.height = 'auto';
                    const maxHeight = window.innerHeight * 0.4;
                    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
                    }}
                />

                <button
                    type="submit"
                    className="
                    absolute bottom-6 right-6 p-2
                    text-blue-600 hover:text-blue-800
                    rounded-full transition
                    "
                >
                    <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-6 h-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                    >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 12h14M12 5l7 7-7 7"
                    />
                    </svg>
                </button>
                </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInput;