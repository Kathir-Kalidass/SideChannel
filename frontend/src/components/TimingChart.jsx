import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function toChartData(history) {
  return history.run.map((run, index) => ({
    run,
    execution_time: history.timing[index] ?? 0,
  }))
}

export default function TimingChart({ history }) {
  const data = toChartData(history)

  return (
    <article className="panel chart-panel">
      <h3>Timing Trace</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line-grid)" />
          <XAxis dataKey="run" stroke="var(--line-axis)" />
          <YAxis stroke="var(--line-axis)" />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="execution_time"
            stroke="var(--line-timing)"
            strokeWidth={2.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </article>
  )
}
