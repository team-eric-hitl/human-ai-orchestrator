import { useAppState } from '@/state/AppState';
import { LineChart, Line, ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, AreaChart, Area } from 'recharts';

function formatTime(t: number): string {
  const d = new Date(t);
  return `${d.getMinutes()}:${String(d.getSeconds()).padStart(2, '0')}`;
}

export default function Charts() {
  const { metrics } = useAppState();
  const data = metrics.sentimentSeries.slice(-60);
  return (
    <div className="grid two-cols">
      <div className="panel" style={{ padding: 16 }}>
        <h3 style={{ marginTop: 0 }}>Customer Sentiment</h3>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ left: 12, right: 12, top: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#23314e" />
              <XAxis dataKey="t" tickFormatter={formatTime} stroke="#93a3b8" />
              <YAxis stroke="#93a3b8" domain={[0, 100]} />
              <Tooltip labelFormatter={(l) => formatTime(l as number)} />
              <Line type="monotone" dataKey="value" stroke="#34d399" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="panel" style={{ padding: 16 }}>
        <h3 style={{ marginTop: 0 }}>Model Latency Distribution</h3>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={[10, 50, 120, 300, 600, 900].map((v, i) => ({ bucket: `${v}ms`, count: Math.max(1, Math.round(Math.random() * 8)) }))}
              margin={{ left: 12, right: 12, top: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#23314e" />
              <XAxis dataKey="bucket" stroke="#93a3b8" />
              <YAxis stroke="#93a3b8" />
              <Area type="monotone" dataKey="count" stroke="#60a5fa" fill="#1d4ed8" fillOpacity={0.2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}


