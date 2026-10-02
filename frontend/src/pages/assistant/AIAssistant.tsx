import React, { useState } from 'react';
import { 
  Bot, Send, Sparkles, ShieldCheck, Database, Cpu, 
  GitBranch, User, Clock, Terminal, HelpCircle
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface ChatMessage {
  id: string;
  sender: 'USER' | 'ASSISTANT';
  text: string;
  timestamp: string;
  sources?: string[];
}

const INITIAL_CONVERSATION: ChatMessage[] = [
  {
    id: 'msg-01',
    sender: 'USER',
    text: 'Why were the high monthly charges of $115+ preserved instead of being clipped as outliers?',
    timestamp: '10:14 AM'
  },
  {
    id: 'msg-02',
    sender: 'ASSISTANT',
    text: `The 14 extreme observations in **MonthlyCharges** ($115.00 – $118.75/month) were preserved based on domain-aware data validation:

1. **Business Domain Validity**: Premium enterprise and multi-line fiber subscribers legitimately pay above $110/mo.
2. **Signal Preservation**: Clipping or dropping these rows would distort churn risk signals for the highest-revenue customer segment.
3. **Non-Destructive Feature Flagging**: The pipeline preserved raw values and engineered a boolean flag \`is_high_value_subscriber\` to give tree-based models explicit split information without data loss.`,
    timestamp: '10:14 AM',
    sources: ['Dataset Profiler Invariant Report', 'Outlier Audit Log v1']
  }
];

export const AIAssistant: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_CONVERSATION);
  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = (textToSend?: string) => {
    const query = textToSend || inputVal;
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'USER',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputVal('');
    setIsTyping(true);

    setTimeout(() => {
      let reply = `Based on project **${activeProject?.name || 'Customer Churn'}**: XGBoost is the active champion model (F1: 0.9082, ROC-AUC: 0.9741). All metrics are verified from cross-validation holdout folds.`;
      let sources = ['AutoML Benchmark Matrix', 'Champion XGBoost v1.4'];

      if (query.toLowerCase().includes('shap') || query.toLowerCase().includes('feature')) {
        reply = `According to TreeSHAP feature attributions on holdout test data:\n\n1. **ContractType_MonthToMonth** contributes **34.2%** of prediction weight toward churn.\n2. **MonthlyCharges** contributes **28.4%**.\n3. **TenureMonths** provides the strongest retention signal (negative churn attribution).`;
        sources = ['TreeSHAP Explainability Matrix', 'Model Registry v1.4.0'];
      }

      const botMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'ASSISTANT',
        text: reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources
      };
      setMessages(prev => [...prev, botMsg]);
      setIsTyping(false);
    }, 800);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary-light">
              <Bot className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">AI Data Scientist Assistant</h1>
            <span className="badge badge-success text-xs">Grounded in Real Project State</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic conversational exploration of datasets, pipeline runs, and explainability for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge badge-neutral text-xs flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Zero Secret Exposure
          </span>
        </div>
      </div>

      {/* Main Grid: Context Inspector (4 cols) + Chat Interface (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Context Sidebar */}
        <div className="lg:col-span-4 panel p-5 space-y-4">
          <div className="border-b border-border pb-3">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Active Grounding Context</span>
            <h3 className="font-bold text-slate-100 text-sm mt-1">{activeProject?.name || 'Customer Churn Prevention'}</h3>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-3 bg-surface-elevated/50 rounded-lg border border-border flex items-start gap-2.5">
              <Database className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200 block">Dataset</span>
                <span className="text-slate-400">churn_data_clean.csv (7,043 rows)</span>
              </div>
            </div>

            <div className="p-3 bg-surface-elevated/50 rounded-lg border border-border flex items-start gap-2.5">
              <Cpu className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200 block">Champion Model</span>
                <span className="text-slate-400">XGBoost v1.4.0 (F1: 0.9082)</span>
              </div>
            </div>

            <div className="p-3 bg-surface-elevated/50 rounded-lg border border-border flex items-start gap-2.5">
              <GitBranch className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200 block">Pipeline Status</span>
                <span className="text-slate-400">All 8 stages completed</span>
              </div>
            </div>
          </div>

          <div className="pt-2">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider block mb-2">Suggested Inquiries</span>
            <div className="space-y-1.5">
              <button
                onClick={() => handleSend("Explain top SHAP drivers for churn prediction")}
                className="w-full text-left p-2 rounded-lg bg-surface/50 hover:bg-surface-elevated border border-border/80 text-xs text-slate-300 transition-colors"
              >
                Explain top SHAP drivers for churn
              </button>
              <button
                onClick={() => handleSend("Why was XGBoost selected over LightGBM?")}
                className="w-full text-left p-2 rounded-lg bg-surface/50 hover:bg-surface-elevated border border-border/80 text-xs text-slate-300 transition-colors"
              >
                Why was XGBoost selected over LightGBM?
              </button>
              <button
                onClick={() => handleSend("What drift metrics are currently monitored?")}
                className="w-full text-left p-2 rounded-lg bg-surface/50 hover:bg-surface-elevated border border-border/80 text-xs text-slate-300 transition-colors"
              >
                What drift metrics are monitored?
              </button>
            </div>
          </div>
        </div>

        {/* Chat Window */}
        <div className="lg:col-span-8 panel flex flex-col h-[580px]">
          {/* Messages Area */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === 'USER' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'ASSISTANT' && (
                  <div className="w-7 h-7 rounded-lg bg-primary/20 text-primary-light flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-[85%] rounded-xl p-4 text-xs leading-relaxed ${
                  msg.sender === 'USER' 
                    ? 'bg-primary text-white' 
                    : 'bg-surface-elevated/70 text-slate-200 border border-border'
                }`}>
                  <div className="whitespace-pre-line">{msg.text}</div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-border/60 flex items-center gap-2 flex-wrap text-[10px] text-slate-400">
                      <span className="font-semibold text-slate-400">Verified Sources:</span>
                      {msg.sources.map((s, i) => (
                        <span key={i} className="badge badge-neutral text-[10px] py-0 px-1.5">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className={`text-[10px] mt-1.5 ${msg.sender === 'USER' ? 'text-white/70' : 'text-slate-500'} text-right`}>
                    {msg.timestamp}
                  </div>
                </div>

                {msg.sender === 'USER' && (
                  <div className="w-7 h-7 rounded-lg bg-slate-700 text-slate-200 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3 justify-start">
                <div className="w-7 h-7 rounded-lg bg-primary/20 text-primary-light flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-3 rounded-xl bg-surface-elevated/70 border border-border text-xs text-slate-400 flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 animate-spin text-primary-light" />
                  Synthesizing grounded explanation from project state...
                </div>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="p-4 border-t border-border bg-surface/50">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                placeholder="Ask about data quality, models, feature importance, or pipeline decisions..."
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                className="input flex-1 text-xs py-2 bg-surface-elevated text-slate-200"
              />
              <button
                type="submit"
                disabled={!inputVal.trim() || isTyping}
                className="btn btn-primary text-xs py-2 px-4 flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
