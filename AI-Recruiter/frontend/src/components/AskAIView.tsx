import React from 'react';
import { Bot, Send, Sparkles } from 'lucide-react';

export default function AskAIView() {
  return (
    <div className="w-full px-10 md:px-16 mt-16 animate-in fade-in duration-300 pb-20 max-w-7xl mx-auto">
      <div className="mb-10">
        <h2 className="text-5xl font-serif font-bold text-[#e6e2db] mb-4 tracking-tight">Ask AI</h2>
        <p className="text-[#8b8680] text-xl">
          Conversational intelligence over your candidate database.
        </p>
      </div>

      <div className="bg-[#1c1a17] border border-[#35312c] rounded-2xl flex flex-col h-[700px] overflow-hidden shadow-xl">
        {/* Header */}
        <div className="bg-[#23211e] border-b border-[#35312c] p-5 flex items-center gap-3">
          <Sparkles className="text-[#9a5633]" size={24} />
          <h3 className="font-semibold text-[#e6e2db] text-xl">AI Assistant</h3>
        </div>

        {/* Chat Area */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="flex gap-5">
            <div className="w-10 h-10 rounded-full bg-[#2a2724] border border-[#35312c] flex items-center justify-center flex-shrink-0 mt-1">
              <Bot size={20} className="text-[#a09c95]" />
            </div>
            <div className="bg-[#23211e] border border-[#35312c] rounded-xl rounded-tl-none p-5 text-[#a09c95] text-base max-w-[80%] leading-relaxed shadow-sm">
              Hello. I'm your AI recruiter assistant. Ask me anything about your talent pool, such as 'Who are our best frontend engineers?' or 'Which candidates have more than 5 years of Python experience?'
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="p-5 bg-[#23211e] border-t border-[#35312c]">
          <div className="relative flex items-center">
            <input 
              type="text" 
              placeholder="Ask a question..." 
              className="w-full bg-[#1c1a17] border border-[#35312c] rounded-xl py-4 px-5 text-[#e6e2db] text-base focus:outline-none focus:border-[#5a544a]"
            />
            <button className="absolute right-3 p-3 bg-[#9a5633] hover:bg-[#b0623a] text-white rounded-lg transition-colors">
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
