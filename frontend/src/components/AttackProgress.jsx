import { useSimulation } from '../context/SimulationContext'

export default function AttackProgress() {
  const { attack, status } = useSimulation()
  const progress = Math.max(0, Math.min(100, attack.attack_progress || 0))

  return (
    <article className="panel attack-progress">
      <h3>Attack Progress</h3>
      <div className="progress-value">{progress.toFixed(1)}%</div>
      <div className="progress-track" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>
      <div className="progress-meta">
        <span>Keys Tested: {attack.keys_tested || 0}</span>
        <span>
          Runs: {status.runs_completed || 0}/{status.total_runs || 0}
        </span>
      </div>
    </article>
  )
}
