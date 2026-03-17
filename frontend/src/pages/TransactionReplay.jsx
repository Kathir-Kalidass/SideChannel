export default function TransactionReplay({ transaction, onBack }) {
  if (!transaction) {
    return (
      <main className="dashboard-shell">
        <section className="panel">
          <h1>Transaction Replay</h1>
          <p className="muted">No transaction selected.</p>
          <button type="button" className="btn" onClick={onBack}>
            Back to Dashboard
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header panel">
        <div className="header-row">
          <p className="eyebrow">Transaction Replay</p>
          <button type="button" className="btn" onClick={onBack}>
            Back
          </button>
        </div>
        <h1>Payment Decision Replay</h1>
        <p>
          INR {transaction.amount} from {transaction.senderName} to {transaction.receiverName} on {transaction.date} at {transaction.time}
        </p>
      </header>

      <section className="app-grid">
        <article className="panel">
          <h2>Decision Summary</h2>
          <div className="live-grid">
            <div className="live-item">
              <span>Decision</span>
              <strong className={`decision decision-${transaction.decision.toLowerCase()}`}>{transaction.decision}</strong>
            </div>
            <div className="live-item">
              <span>Risk</span>
              <strong>{(transaction.risk * 100).toFixed(1)}%</strong>
            </div>
            <div className="live-item">
              <span>Leakage</span>
              <strong>{transaction.leakage.toFixed(3)}</strong>
            </div>
            <div className="live-item">
              <span>Correlation</span>
              <strong>{transaction.correlation.toFixed(3)}</strong>
            </div>
            <div className="live-item">
              <span>Algorithm</span>
              <strong>{transaction.algorithm}</strong>
            </div>
            <div className="live-item">
              <span>Defense</span>
              <strong>{transaction.defense ? 'ON' : 'OFF'}</strong>
            </div>
            <div className="live-item">
              <span>Attacker Port</span>
              <strong>{transaction.attackerEnabled ? transaction.attackerPort : 'OFF'}</strong>
            </div>
            <div className="live-item">
              <span>Theft Amount</span>
              <strong>{transaction.decision === 'THEFTED' ? `INR ${transaction.theftAmount}` : '0'}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Transaction Details</h2>
          <div className="timeline-table">
            <div className="timeline-row">
              <span>Sender UPI</span>
              <span>{transaction.senderUpi}</span>
              <span>Amount</span>
              <span>INR {transaction.amount}</span>
            </div>
            <div className="timeline-row">
              <span>Receiver UPI</span>
              <span>{transaction.receiverUpi}</span>
              <span>Ports</span>
              <span>
                {transaction.senderPort} {'->'} {transaction.receiverPort}
              </span>
            </div>
            <div className="timeline-row">
              <span>Note</span>
              <span>{transaction.note || 'No note'}</span>
              <span>OTP Verified</span>
              <span>{transaction.otpVerified ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </article>
      </section>

      <section className="panel">
        <h2>Security Timeline Replay</h2>
        <div className="timeline-table">
          {(transaction.timeline || []).length === 0 ? (
            <p className="muted">No timeline samples available for this payment.</p>
          ) : (
            transaction.timeline.map((step) => (
              <div key={`step-${step.run}`} className="timeline-row">
                <span>Run {step.run}</span>
                <span>Power {step.power.toFixed(2)}</span>
                <span>Time {step.timing.toFixed(3)} ms</span>
                <span>Corr {step.correlation.toFixed(3)}</span>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="panel">
        <h2>Decision Reasoning</h2>
        {!transaction.reasons || transaction.reasons.length === 0 ? (
          <p className="muted">No reasoning details available for this transaction.</p>
        ) : (
          <div className="reason-box">
            <ul>
              {transaction.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </main>
  )
}
