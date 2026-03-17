import { useSimulation } from '../context/SimulationContext'

const TECHNIQUES = ['masking', 'noise_injection', 'constant_time']

export default function DefensePanel() {
  const { defense, onActivateDefense, onDisableDefense, loading } = useSimulation()

  return (
    <section className="panel defense-panel">
      <div className="panel-title-row">
        <h2>Defense Panel</h2>
        <span className={`badge ${defense.defense_mode === 'ACTIVE' ? 'status-running' : 'status-idle'}`}>
          {defense.defense_mode || 'INACTIVE'}
        </span>
      </div>

      <div className="defense-stats">
        <div>
          <span>Technique</span>
          <strong>{defense.technique || 'none'}</strong>
        </div>
        <div>
          <span>Security Level</span>
          <strong>{defense.security_level || 'MEDIUM'}</strong>
        </div>
        <div>
          <span>Leakage Reduction</span>
          <strong>{(defense.leakage_reduction || 0).toFixed(2)}</strong>
        </div>
      </div>

      <div className="button-row">
        {TECHNIQUES.map((technique) => (
          <button
            key={technique}
            type="button"
            className="btn"
            onClick={() => onActivateDefense(technique)}
            disabled={loading}
          >
            Activate {technique}
          </button>
        ))}
        <button type="button" className="btn btn-danger" onClick={onDisableDefense} disabled={loading}>
          Disable Defense
        </button>
      </div>
    </section>
  )
}
