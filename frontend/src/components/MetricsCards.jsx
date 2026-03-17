import { useSimulation } from '../context/SimulationContext'

function metric(value, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '--'
  return Number(value).toFixed(digits)
}

function section(title, items) {
  return (
    <article className="metric-section" key={title}>
      <h3>{title}</h3>
      <div className="metric-list">
        {items.map((item) => (
          <div className="metric-item" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </article>
  )
}

export default function MetricsCards() {
  const { metrics, attack, ai, status } = useSimulation()

  const sections = [
    {
      title: 'Encryption Metrics',
      items: [
        { label: 'Execution Time (ms)', value: metric(metrics.execution_time_ms, 3) },
        { label: 'CPU Usage (%)', value: metric(metrics.cpu_usage_pct) },
        { label: 'Memory Usage (MB)', value: metric(metrics.memory_usage_mb) },
        { label: 'Clock Cycles', value: metric(metrics.clock_cycles, 0) },
      ],
    },
    {
      title: 'Leakage Metrics',
      items: [
        { label: 'Power Avg', value: metric(metrics.power_avg) },
        { label: 'Power Peak', value: metric(metrics.power_peak) },
        { label: 'Hamming Weight', value: metric(metrics.hamming_weight_mean, 2) },
        { label: 'Leakage Score', value: metric(metrics.leakage_score) },
      ],
    },
    {
      title: 'Attack Metrics',
      items: [
        { label: 'Best Key Guess', value: attack.best_key_guess || '--' },
        { label: 'Correlation', value: metric(attack.correlation || metrics.correlation_score) },
        { label: 'Keys Tested', value: metric(attack.keys_tested, 0) },
        { label: 'Progress (%)', value: metric(attack.attack_progress) },
      ],
    },
    {
      title: 'Cache Metrics',
      items: [
        { label: 'Cache Hits', value: metric(metrics.cache_hits, 0) },
        { label: 'Cache Misses', value: metric(metrics.cache_misses, 0) },
        { label: 'Miss Rate (%)', value: metric(metrics.cache_miss_rate) },
        { label: 'Runs Completed', value: metric(status.runs_completed, 0) },
      ],
    },
    {
      title: 'AI Security Intelligence',
      items: [
        { label: 'Leakage Risk', value: ai.risk_level || metrics.risk_level || 'LOW' },
        { label: 'Attack Probability (%)', value: metric((ai.attack_probability || metrics.attack_probability) * 100) },
        { label: 'Model Confidence (%)', value: metric((ai.model_confidence || metrics.model_confidence) * 100) },
        { label: 'Correlation Score', value: metric(metrics.correlation_score) },
      ],
    },
  ]

  return <section className="metrics-grid">{sections.map((s) => section(s.title, s.items))}</section>
}
