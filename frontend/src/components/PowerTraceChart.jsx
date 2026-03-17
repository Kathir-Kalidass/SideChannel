import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function toChartData(trace) {
  return trace.map((value, index) => ({
    step: index + 1,
    power: value ?? 0,
  }))
}

export default function PowerTraceChart({ trace }) {
  const data = toChartData(trace || [])

  return (
    <article className="panel chart-panel">
      <h3>Power Trace</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line-grid)" />
          <XAxis dataKey="step" stroke="var(--line-axis)" />
          <YAxis stroke="var(--line-axis)" />
          <Tooltip />
          <Line type="monotone" dataKey="power" stroke="var(--line-power)" strokeWidth={2.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </article>
  )
}
