import AgentsTable from '@/components/AgentsTable';
import Charts from '@/components/Charts';
import MetricCards from '@/components/MetricCards';

export default function DashboardPage() {
  return (
    <div className="container grid" style={{ gap: 16 }}>
      <MetricCards />
      <Charts />
      <AgentsTable />
    </div>
  );
}




