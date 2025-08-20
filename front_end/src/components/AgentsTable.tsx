import { useAppState } from '@/state/AppState';

export default function AgentsTable() {
  const { agents } = useAppState();
  return (
    <div className="panel" style={{ padding: 16 }}>
      <h3 style={{ marginTop: 0 }}>Human Agents</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Skills</th>
            <th>Queue</th>
            <th>Satisfaction</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((a) => (
            <tr key={a.id}>
              <td>{a.name}</td>
              <td>{a.online ? <span className="tag green">Online</span> : <span className="tag red">Offline</span>}</td>
              <td className="muted">{a.skills.join(', ')}</td>
              <td>{a.queueSize}</td>
              <td>{a.satisfactionScore}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}




