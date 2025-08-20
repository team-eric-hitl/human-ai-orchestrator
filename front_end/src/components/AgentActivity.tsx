import { useAppState } from '@/state/AppState';

export default function AgentActivity() {
  const { conversations } = useAppState();
  const conv = conversations[0];
  return (
    <div className="panel" style={{ padding: 16, height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Improvement Module Activity</h3>
      </div>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {conv.events.map((e) => (
          <li key={e.id} className="bubble agent">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong style={{ textTransform: 'capitalize' }}>{e.kind}</strong>
              {typeof e.score === 'number' && (
                <span className={`tag ${e.kind === 'frustration' ? (e.score >= 60 ? 'red' : 'green') : 'blue'}`}>{
                  e.kind === 'frustration' ? `score ${e.score}` : e.kind === 'quality' ? `conf ${Math.round((e.score ?? 0) * 100)}%` : ''
                }</span>
              )}
            </div>
            <div className="muted" style={{ marginTop: 4 }}>{e.description}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}




