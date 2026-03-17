import { useMemo } from 'react'
import { useSimulation } from '../context/SimulationContext'

const ALGORITHMS = ['AES', 'RSA', 'ECC', 'ChaCha20']
const ATTACK_TYPES = ['power', 'timing', 'cache']

export default function ControlPanel() {
  const {
    config,
    setConfig,
    onStart,
    onStop,
    onReset,
    onTrainAI,
    onExportDataset,
    loading,
    status,
    socketState,
  } = useSimulation()

  const statusLabel = useMemo(() => {
    if (status.status === 'running') return 'RUNNING'
    if (status.status === 'stopped') return 'STOPPED'
    return 'IDLE'
  }, [status.status])

  const update = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <section className="panel control-panel">
      <div className="panel-title-row">
        <h2>Control Panel</h2>
        <div className="state-badges">
          <span className={`badge status-${statusLabel.toLowerCase()}`}>{statusLabel}</span>
          <span className={`badge socket-${socketState}`}>WS {socketState.toUpperCase()}</span>
        </div>
      </div>

      <div className="grid-4">
        <label>
          Algorithm
          <select value={config.algorithm} onChange={(e) => update('algorithm', e.target.value)}>
            {ALGORITHMS.map((algorithm) => (
              <option key={algorithm} value={algorithm}>
                {algorithm}
              </option>
            ))}
          </select>
        </label>

        <label>
          Attack Type
          <select value={config.attack_type} onChange={(e) => update('attack_type', e.target.value)}>
            {ATTACK_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <label>
          Runs
          <input
            type="number"
            min={10}
            step={10}
            value={config.runs}
            onChange={(e) => update('runs', Number(e.target.value))}
          />
        </label>

        <div className="toggle-wrap">
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={config.enable_ai}
              onChange={(e) => update('enable_ai', e.target.checked)}
            />
            Enable AI
          </label>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={config.auto_defense}
              onChange={(e) => update('auto_defense', e.target.checked)}
            />
            Auto Defense
          </label>
        </div>
      </div>

      <div className="button-row">
        <button type="button" className="btn btn-primary" onClick={onStart} disabled={loading}>
          Start Simulation
        </button>
        <button type="button" className="btn" onClick={onStop} disabled={loading}>
          Stop
        </button>
        <button type="button" className="btn" onClick={onReset} disabled={loading}>
          Reset
        </button>
        <button type="button" className="btn btn-secondary" onClick={onTrainAI} disabled={loading}>
          Train AI
        </button>
        <button type="button" className="btn" onClick={onExportDataset} disabled={loading}>
          Export Dataset
        </button>
      </div>
    </section>
  )
}
