import { useAppState } from '@/state/AppState';

function StatusBadge({ ok }: { ok: boolean }) {
  return <span className={`badge ${ok ? 'green' : 'red'}`}>{ok ? '✓' : '!'}</span>;
}

export default function MetricCards() {
  const { metrics } = useAppState();
  const cards: { label: string; value: string; tag?: string }[] = [
    { label: 'Active Conversations', value: String(metrics.activeConversations) },
    { label: 'Escalations to Humans', value: String(metrics.escalationsToHumans), tag: metrics.escalationsToHumans > 0 ? 'red' : 'green' },
    { label: 'Avg First Response', value: `${metrics.avgFirstResponseMs} ms` },
    { label: 'Customer Satisfaction', value: `${metrics.csat}%`, tag: metrics.csat >= 90 ? 'green' : 'red' },
    { label: 'Model Latency', value: `${metrics.modelLatencyMs} ms` },
    { label: 'Avg Tokens', value: `${metrics.avgTokens}` }
  ];
  return (
    <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
      {cards.map((c) => (
        <div key={c.label} className="panel" style={{ padding: 16 }}>
          <div className="metric">
            <div>
              <div className="muted" style={{ fontSize: 12 }}>{c.label}</div>
              <div style={{ fontSize: 22, fontWeight: 700 }}>{c.value}</div>
            </div>
            {c.tag && <StatusBadge ok={c.tag === 'green'} />}
          </div>
        </div>
      ))}
    </div>
  );
}


