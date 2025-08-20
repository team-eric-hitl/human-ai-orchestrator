import { useRef, useState, useEffect } from 'react';
import { useAppState } from '@/state/AppState';
import { Message } from '@/types';

function Bubble({ m }: { m: Message }) {
  return (
    <div className={`bubble ${m.role}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="tag blue" style={{ textTransform: 'capitalize' }}>{m.role}</span>
        <span className="muted" style={{ fontSize: 12 }}>{new Date(m.timestamp).toLocaleTimeString()}</span>
      </div>
      <div style={{ marginTop: 6, whiteSpace: 'pre-wrap' }}>{m.text}</div>
    </div>
  );
}

export default function ChatWindow() {
  const { conversations, sendUserMessage } = useAppState();
  const conv = conversations[0];
  const [text, setText] = useState('');
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [conv.messages.length]);

  async function onSend() {
    const trimmed = text.trim();
    if (!trimmed) return;
    setText('');
    await sendUserMessage(trimmed);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="panel chat" style={{ height: '100%' }}>
      <div className="messages" ref={listRef}>
        {conv.messages.map((m) => (
          <Bubble m={m} key={m.id} />
        ))}
      </div>
      <div className="composer">
        <textarea
          className="input"
          rows={2}
          placeholder="Ask about your coverage, deductible, claims, ID card, premium, or cancellations..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button className="btn" onClick={onSend}>Send</button>
      </div>
    </div>
  );
}




