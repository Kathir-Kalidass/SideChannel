import { useSimulation } from '../context/SimulationContext'

export default function AttackLog() {
  const { attackLog } = useSimulation()

  return (
    <section className="panel attack-log">
      <h2>Attack Log</h2>
      <ul>
        {attackLog.length === 0 ? (
          <li>No attack logs yet. Start simulation to stream events.</li>
        ) : (
          attackLog.map((entry, index) => <li key={`${entry}-${index}`}>{entry}</li>)
        )}
      </ul>
    </section>
  )
}
