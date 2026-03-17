import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function CorrelationChart({ profile }) {
  return (
    <article className="panel chart-panel chart-panel-wide">
      <h3>Correlation Graph</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={profile || []}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line-grid)" />
          <XAxis dataKey="key_guess" stroke="var(--line-axis)" />
          <YAxis stroke="var(--line-axis)" domain={[0, 1]} />
          <Tooltip />
          <Bar
            dataKey="correlation"
            fill="var(--line-correlation-fill)"
            stroke="var(--line-correlation)"
          />
        </BarChart>
      </ResponsiveContainer>
    </article>
  )
}
