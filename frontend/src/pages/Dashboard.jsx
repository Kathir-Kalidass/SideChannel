import { useMemo, useState } from 'react'
import { useSimulation } from '../context/SimulationContext'
import { getAIPrediction, getAdaptivePolicy, getCurrentMetrics } from '../services/api'

const THRESHOLDS = {
  blockProbability: 0.86,
  blockLeakage: 0.78,
  otpProbability: 0.52,
  otpLeakage: 0.56,
}

function generateOtp() {
  return String(Math.floor(100000 + Math.random() * 900000))
}

function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value))
}

function getDecision({ scenarioRisk, leakageScore, attackerEnabled, senderOtpEnabled, receiverOtpEnabled, thresholds }) {
  if (scenarioRisk >= thresholds.blockProbability || leakageScore >= thresholds.blockLeakage) {
    return 'BLOCK'
  }

  if (attackerEnabled && scenarioRisk >= 0.7 && !senderOtpEnabled && !receiverOtpEnabled) {
    return 'THEFT'
  }

  if (senderOtpEnabled || receiverOtpEnabled || scenarioRisk >= thresholds.otpProbability || leakageScore >= thresholds.otpLeakage) {
    return 'OTP'
  }

  return 'APPROVE'
}

function buildDecisionReasons({
  scenarioRisk,
  baseAttackProbability,
  leakageScore,
  amountValue,
  amountFactor,
  vulnerabilityFactor,
  attackFactor,
  otpProtection,
  attackerEnabled,
  attackerPort,
  decision,
  sender,
  receiver,
  thresholds,
  adaptive,
}) {
  const reasons = [
    `Combined risk score: ${(scenarioRisk * 100).toFixed(1)}%`,
    `AI attack probability contribution: ${(baseAttackProbability * 100).toFixed(1)}%`,
    `Leakage score contribution: ${leakageScore.toFixed(3)}`,
    `Amount impact for INR ${amountValue.toFixed(2)}: +${(amountFactor * 100).toFixed(1)}%`,
    `Endpoint vulnerability (sender/receiver): +${(vulnerabilityFactor * 100).toFixed(1)}%`,
    `OTP protection deduction: -${(otpProtection * 100).toFixed(1)}%`,
    `Adaptive thresholds: BLOCK ${Math.round(thresholds.blockProbability * 100)}%, OTP ${Math.round(thresholds.otpProbability * 100)}%`,
  ]

  if (adaptive) {
    reasons.push(
      `Adaptive multipliers -> sender ${adaptive.senderMultiplier.toFixed(2)}x, receiver ${adaptive.receiverMultiplier.toFixed(2)}x, pair ${adaptive.pairMultiplier.toFixed(2)}x`,
    )
    reasons.push(
      `Drift scores -> sender ${(adaptive.senderDrift * 100).toFixed(1)}%, receiver ${(adaptive.receiverDrift * 100).toFixed(1)}%`,
    )
  }

  if (attackerEnabled) {
    reasons.push(`Active attacker route on port ${attackerPort}: +${(attackFactor * 100).toFixed(1)}%`)
  }

  if (sender?.otpEnabled) {
    reasons.push(`Sender ${sender.name} has OTP protection enabled.`)
  }
  if (receiver?.otpEnabled) {
    reasons.push(`Receiver ${receiver.name} has OTP protection enabled.`)
  }

  if (decision === 'BLOCK') {
    reasons.push('Final decision BLOCK because risk crossed hard threshold 86%.')
  }
  if (decision === 'THEFT') {
    reasons.push('Final decision THEFT because attacker path was active with insufficient OTP protection.')
  }
  if (decision === 'OTP') {
    reasons.push('Final decision OTP because transaction requires step-up verification.')
  }
  if (decision === 'APPROVE') {
    reasons.push('Final decision APPROVE because combined risk stayed within safe bounds.')
  }

  return reasons
}

export default function Dashboard({ transactions, onAddTransaction, onOpenReplay, user, onLogout, users }) {
  const {
    ai,
    attack,
    attackLog,
    config,
    error,
    history,
    metrics,
    onStart,
    onStop,
    refreshSnapshot,
    setConfig,
    socketState,
    status,
  } = useSimulation()

  const sender = useMemo(() => users.find((entry) => entry.id === user.id) || user, [user, users])
  const receiverOptions = useMemo(() => users.filter((entry) => entry.id !== sender.id), [sender.id, users])

  const [payment, setPayment] = useState({
    receiverId: receiverOptions[0]?.id || '',
    amount: '1250',
    note: 'UPI Transfer',
    attackerEnabled: true,
    attackerPort: '7103',
    attackerIntensity: 'high',
  })
  const [scan, setScan] = useState({
    open: false,
    phase: 'idle',
    progress: 0,
    decision: null,
    otpVerified: false,
    otpCode: '',
    otpInput: '',
    otpError: '',
    riskSnapshot: 0,
    leakageSnapshot: 0,
    baseAttackSnapshot: 0,
    receiverId: '',
    reasons: [],
    adaptivePolicy: null,
    message: '',
  })

  const receiver = useMemo(
    () => users.find((entry) => entry.id === payment.receiverId) || receiverOptions[0] || null,
    [payment.receiverId, receiverOptions, users],
  )

  const liveMetrics = useMemo(
    () => [
      { label: 'Attack Probability', value: `${((ai.attack_probability || 0) * 100).toFixed(1)}%` },
      { label: 'Leakage Score', value: Number(metrics.leakage_score || 0).toFixed(3) },
      { label: 'Correlation', value: Number(metrics.correlation_score || 0).toFixed(3) },
      { label: 'Defense', value: status.defense_mode ? 'ON' : 'OFF' },
      { label: 'Risk Level', value: ai.risk_level || 'LOW' },
      { label: 'Socket', value: socketState },
    ],
    [ai.attack_probability, ai.risk_level, metrics.correlation_score, metrics.leakage_score, socketState, status.defense_mode],
  )

  const onPaymentChange = (field, value) => {
    setPayment((prev) => ({ ...prev, [field]: value }))
  }

  const closeModal = () => {
    setScan({
      open: false,
      phase: 'idle',
      progress: 0,
      decision: null,
      otpVerified: false,
      otpCode: '',
      otpInput: '',
      otpError: '',
      riskSnapshot: 0,
      leakageSnapshot: 0,
      baseAttackSnapshot: 0,
      receiverId: '',
      reasons: [],
      adaptivePolicy: null,
      message: '',
    })
  }

  const pushTransaction = ({
    decision,
    otpVerified = false,
    riskInput = 0,
    leakageInput = 0,
    baseAttackInput = 0,
    receiverIdInput = '',
    theftAmount = 0,
    reasons = [],
  }) => {
    const now = new Date()
    const selectedReceiver = users.find((entry) => entry.id === receiverIdInput) || receiver
    const timeline = (history.run || []).slice(-12).map((run, index, list) => {
      const i = history.run.length - list.length + index
      return {
        run,
        power: Number(history.power[i] || 0),
        timing: Number(history.timing[i] || 0),
        correlation: Number(history.correlation[i] || 0),
      }
    })

    onAddTransaction({
      id: `${now.getTime()}-${Math.random().toString(16).slice(2)}`,
      time: now.toLocaleTimeString(),
      date: now.toLocaleDateString(),
      senderUserId: sender.id,
      senderName: sender.name,
      senderUpi: sender.upi,
      senderPort: sender.port,
      receiverUserId: selectedReceiver?.id || 0,
      receiverName: selectedReceiver?.name || 'Unknown',
      receiverUpi: selectedReceiver?.upi || 'unknown@upi',
      receiverPort: selectedReceiver?.port || 0,
      amount: payment.amount,
      note: payment.note,
      algorithm: config.algorithm,
      decision,
      otpVerified,
      risk: Number(riskInput),
      leakage: Number(leakageInput),
      baseAttack: Number(baseAttackInput),
      correlation: Number(metrics.correlation_score || 0),
      defense: Boolean(status.defense_mode),
      attackerEnabled: payment.attackerEnabled,
      attackerPort: Number(payment.attackerPort || 7103),
      theftAmount,
      senderOtpEnabled: Boolean(sender.otpEnabled),
      receiverOtpEnabled: Boolean(selectedReceiver?.otpEnabled),
      reasons,
      timeline,
    })
  }

  const onInitiatePayment = async (event) => {
    event.preventDefault()
    if (!receiver) {
      return
    }

    setConfig((prev) => ({ ...prev, algorithm: config.algorithm || 'AES', attack_type: 'power', runs: 120 }))
    setScan({
      open: true,
      phase: 'scanning',
      progress: 5,
      decision: null,
      otpVerified: false,
      otpCode: '',
      otpInput: '',
      otpError: '',
      riskSnapshot: 0,
      leakageSnapshot: 0,
      baseAttackSnapshot: 0,
      receiverId: receiver.id,
      reasons: [],
      adaptivePolicy: null,
      message: `Scanning payment route from ${sender.port} to ${receiver.port}...`,
    })

    try {
      await onStart()

      for (let step = 1; step <= 6; step += 1) {
        await new Promise((resolve) => {
          setTimeout(resolve, 600)
        })
        await refreshSnapshot()
        setScan((prev) => ({
          ...prev,
          progress: Math.min(95, step * 15),
        }))
      }

      const [freshAi, freshMetrics, policy] = await Promise.all([
        getAIPrediction(),
        getCurrentMetrics(),
        getAdaptivePolicy(sender.id, receiver.id),
      ])
      const amountValue = Number(payment.amount || 0)
      const baseAttackProbability = Number(freshAi?.attack_probability || 0)
      const leakageScore = Number(freshMetrics?.leakage_score || 0)

      const amountFactor = clamp(amountValue / 80000, 0, 0.35)
      const vulnerabilityFactor = clamp(((sender.vulnerability || 0) + (receiver.vulnerability || 0)) / 2, 0, 0.35)
      const attackFactor = payment.attackerEnabled
        ? payment.attackerIntensity === 'high'
          ? 0.32
          : payment.attackerIntensity === 'medium'
            ? 0.22
            : 0.12
        : 0
      const otpProtection = (sender.otpEnabled ? 0.13 : 0) + (receiver.otpEnabled ? 0.13 : 0)

      const senderMultiplier = Number(policy?.sender?.risk_multiplier || 1)
      const receiverMultiplier = Number(policy?.receiver?.risk_multiplier || 1)
      const pairMultiplier = Number(policy?.pair?.risk_multiplier || 1)
      const adaptiveComposite = clamp(senderMultiplier * 0.35 + receiverMultiplier * 0.25 + pairMultiplier * 0.4, 0.75, 2.2)

      const dynamicThresholds = {
        blockProbability: Number(policy?.thresholds?.block_threshold || THRESHOLDS.blockProbability),
        otpProbability: Number(policy?.thresholds?.otp_threshold || THRESHOLDS.otpProbability),
        blockLeakage: Number(policy?.thresholds?.leakage_block_threshold || THRESHOLDS.blockLeakage),
        otpLeakage: Number(policy?.thresholds?.leakage_otp_threshold || THRESHOLDS.otpLeakage),
      }

      const scenarioRisk = clamp(
        (
          baseAttackProbability * 0.45 + leakageScore * 0.4 + amountFactor + vulnerabilityFactor + attackFactor - otpProtection
        ) * adaptiveComposite,
      )

      const decision = getDecision({
        scenarioRisk,
        leakageScore,
        attackerEnabled: Boolean(payment.attackerEnabled),
        senderOtpEnabled: Boolean(sender.otpEnabled),
        receiverOtpEnabled: Boolean(receiver.otpEnabled),
        thresholds: dynamicThresholds,
      })

      const reasons = buildDecisionReasons({
        scenarioRisk,
        baseAttackProbability,
        leakageScore,
        amountValue,
        amountFactor,
        vulnerabilityFactor,
        attackFactor,
        otpProtection,
        attackerEnabled: Boolean(payment.attackerEnabled),
        attackerPort: payment.attackerPort,
        decision,
        sender,
        receiver,
        thresholds: dynamicThresholds,
        adaptive: {
          senderMultiplier,
          receiverMultiplier,
          pairMultiplier,
          senderDrift: Number(policy?.sender?.drift_score || 0),
          receiverDrift: Number(policy?.receiver?.drift_score || 0),
        },
      })

      await onStop()

      if (decision === 'APPROVE') {
        pushTransaction({
          decision: 'APPROVED',
          otpVerified: false,
          riskInput: scenarioRisk,
          leakageInput: leakageScore,
          baseAttackInput: baseAttackProbability,
          receiverIdInput: receiver.id,
          reasons,
        })
        setScan({
          open: true,
          phase: 'done',
          progress: 100,
          decision,
          otpVerified: false,
          otpCode: '',
          otpInput: '',
          otpError: '',
          riskSnapshot: scenarioRisk,
          leakageSnapshot: leakageScore,
          baseAttackSnapshot: baseAttackProbability,
          receiverId: receiver.id,
          reasons,
          adaptivePolicy: policy,
          message: 'Payment approved and transferred safely.',
        })
        return
      }

      if (decision === 'OTP') {
        const otpCode = generateOtp()
        setScan({
          open: true,
          phase: 'otp',
          progress: 100,
          decision,
          otpVerified: false,
          otpCode,
          otpInput: '',
          otpError: '',
          riskSnapshot: scenarioRisk,
          leakageSnapshot: leakageScore,
          baseAttackSnapshot: baseAttackProbability,
          receiverId: receiver.id,
          reasons,
          adaptivePolicy: policy,
          message: `Risk detected on route ${sender.port} -> ${receiver.port}. Verify OTP to continue. Demo OTP: 123456`,
        })
        return
      }

      if (decision === 'THEFT') {
        const theftAmount = Number((Number(payment.amount || 0) * 0.8).toFixed(2))
        pushTransaction({
          decision: 'THEFTED',
          otpVerified: false,
          riskInput: scenarioRisk,
          leakageInput: leakageScore,
          baseAttackInput: baseAttackProbability,
          receiverIdInput: receiver.id,
          theftAmount,
          reasons,
        })
        setScan({
          open: true,
          phase: 'done',
          progress: 100,
          decision,
          otpVerified: false,
          otpCode: '',
          otpInput: '',
          otpError: '',
          riskSnapshot: scenarioRisk,
          leakageSnapshot: leakageScore,
          baseAttackSnapshot: baseAttackProbability,
          receiverId: receiver.id,
          reasons,
          adaptivePolicy: policy,
          message: `Attack on port ${payment.attackerPort} intercepted this transaction. Theft simulated: INR ${theftAmount}.`,
        })
        return
      }

      pushTransaction({
        decision: 'BLOCKED',
        otpVerified: false,
        riskInput: scenarioRisk,
        leakageInput: leakageScore,
        baseAttackInput: baseAttackProbability,
        receiverIdInput: receiver.id,
        reasons,
      })
      setScan({
        open: true,
        phase: 'done',
        progress: 100,
        decision,
        otpVerified: false,
        otpCode: '',
        otpInput: '',
        otpError: '',
        riskSnapshot: scenarioRisk,
        leakageSnapshot: leakageScore,
        baseAttackSnapshot: baseAttackProbability,
        receiverId: receiver.id,
        reasons,
        adaptivePolicy: policy,
        message: 'High risk detected. Transfer blocked before settlement.',
      })
    } catch {
      await onStop()
      setScan({
        open: true,
        phase: 'done',
        progress: 100,
        decision: 'BLOCK',
        otpVerified: false,
        otpCode: '',
        otpInput: '',
        otpError: '',
        riskSnapshot: 1,
        leakageSnapshot: 1,
        baseAttackSnapshot: 1,
        receiverId: receiver?.id || '',
        reasons: ['Simulation failed or route unavailable. Blocking transfer by safety policy.'],
        adaptivePolicy: null,
        message: 'Unable to complete risk scan. Transaction blocked.',
      })
    }
  }

  const onOtpChange = (value) => {
    const clean = value.replace(/\D/g, '').slice(0, 6)
    setScan((prev) => ({
      ...prev,
      otpInput: clean,
      otpError: '',
    }))
  }

  const onOtpConfirm = () => {
    if (scan.otpInput.length !== 6) {
      setScan((prev) => ({
        ...prev,
        otpError: 'Enter a valid 6-digit OTP.',
      }))
      return
    }

    const expected = scan.otpCode || '123456'
    if (scan.otpInput !== expected && scan.otpInput !== '123456') {
      setScan((prev) => ({
        ...prev,
        otpError: 'Incorrect OTP. Please try again.',
      }))
      return
    }

    pushTransaction({
      decision: 'APPROVED',
      otpVerified: true,
      riskInput: scan.riskSnapshot,
      leakageInput: scan.leakageSnapshot,
      baseAttackInput: scan.baseAttackSnapshot,
      receiverIdInput: scan.receiverId,
      reasons: scan.reasons,
    })
    setScan((prev) => ({
      ...prev,
      phase: 'done',
      otpVerified: true,
      otpError: '',
      message: 'OTP verified. Payment approved and sent successfully.',
    }))
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header panel">
        <div className="header-row">
          <p className="eyebrow">UPI Payment Authorization Guard</p>
          <div className="header-actions">
            <span className="muted">Signed in as {user?.name || 'User'}</span>
            <button type="button" className="btn" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>
        <h1>Real-Time Secure Transfer</h1>
        <p>Simple payment experience with a live cryptographic risk scan before every authorization.</p>
        {error ? <div className="error-banner">{error}</div> : null}
      </header>

      <section className="app-grid">
        <article className="panel payment-card">
          <h2>Initiate Transfer</h2>
          <div className="port-strip">
            <div className="port-card">
              <span>Sender Port</span>
              <strong>{sender.port}</strong>
              <small>{sender.name}</small>
            </div>
            <div className="port-card">
              <span>Receiver Port</span>
              <strong>{receiver?.port || '--'}</strong>
              <small>{receiver?.name || 'Select receiver'}</small>
            </div>
            <div className="port-card">
              <span>Attacker Port</span>
              <strong>{payment.attackerEnabled ? payment.attackerPort : 'OFF'}</strong>
              <small>{payment.attackerEnabled ? 'Simulated active path' : 'Disabled'}</small>
            </div>
          </div>
          <form className="payment-form" onSubmit={onInitiatePayment}>
            <label>
              Sender (Logged-in User)
              <input value={`${sender.name} (${sender.upi})`} disabled />
            </label>
            <label>
              Receiver
              <select
                value={payment.receiverId}
                onChange={(e) => onPaymentChange('receiverId', e.target.value)}
                required
              >
                {receiverOptions.map((entry) => (
                  <option key={entry.id} value={entry.id}>
                    {entry.name} - {entry.upi}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Amount (INR)
              <input
                type="number"
                min="1"
                value={payment.amount}
                onChange={(e) => onPaymentChange('amount', e.target.value)}
                required
              />
            </label>
            <label>
              Note
              <input value={payment.note} onChange={(e) => onPaymentChange('note', e.target.value)} />
            </label>
            <label>
              Attacker Simulation
              <select
                value={payment.attackerEnabled ? payment.attackerIntensity : 'off'}
                onChange={(e) => {
                  if (e.target.value === 'off') {
                    setPayment((prev) => ({ ...prev, attackerEnabled: false, attackerIntensity: 'low' }))
                    return
                  }
                  setPayment((prev) => ({ ...prev, attackerEnabled: true, attackerIntensity: e.target.value }))
                }}
              >
                <option value="off">Off</option>
                <option value="low">On - Low</option>
                <option value="medium">On - Medium</option>
                <option value="high">On - High</option>
              </select>
            </label>
            <label>
              Security Algorithm
              <select
                value={config.algorithm}
                onChange={(e) => setConfig((prev) => ({ ...prev, algorithm: e.target.value }))}
              >
                <option value="AES">AES</option>
                <option value="ChaCha20">ChaCha20</option>
                <option value="RSA">RSA</option>
                <option value="ECC">ECC</option>
              </select>
            </label>
            <label>
              Attacker Port
              <input
                value={payment.attackerPort}
                onChange={(e) => onPaymentChange('attackerPort', e.target.value.replace(/\D/g, '').slice(0, 5))}
                disabled={!payment.attackerEnabled}
              />
            </label>
            <button type="submit" className="btn btn-primary">
              Pay Now
            </button>
          </form>
        </article>

        <article className="panel live-card">
          <h2>Live Risk Monitor</h2>
          <div className="live-grid">
            {liveMetrics.map((item) => (
              <div key={item.label} className="live-item">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>

          <h3 className="section-heading">Simulation Timeline</h3>
          <div className="timeline-table">
            {(history.run || []).slice(-8).map((run, index, list) => {
              const i = history.run.length - list.length + index
              return (
                <div key={`run-${run}`} className="timeline-row">
                  <span>Run {run}</span>
                  <span>Power {Number(history.power[i] || 0).toFixed(2)}</span>
                  <span>Time {Number(history.timing[i] || 0).toFixed(3)} ms</span>
                  <span>Corr {Number(history.correlation[i] || 0).toFixed(3)}</span>
                </div>
              )
            })}
            {history.run.length === 0 ? <p className="muted">No simulation data yet.</p> : null}
          </div>
        </article>
      </section>

      <section className="panel attack-card">
        <h2>Attack Simulation (Live)</h2>
        <div className="live-grid">
          <div className="live-item">
            <span>Attack Progress</span>
            <strong>{Number(attack.attack_progress || 0).toFixed(1)}%</strong>
          </div>
          <div className="live-item">
            <span>Keys Tested</span>
            <strong>{Number(attack.keys_tested || 0).toFixed(0)}</strong>
          </div>
          <div className="live-item">
            <span>Best Key Guess</span>
            <strong>{attack.best_key_guess || '--'}</strong>
          </div>
        </div>

        <div className="progress-track soft">
          <div className="progress-fill" style={{ width: `${Math.min(100, Number(attack.attack_progress || 0))}%` }}></div>
        </div>

        <h3 className="section-heading">Top Correlation Candidates</h3>
        <div className="timeline-table">
          {(attack.correlation_profile || []).slice(0, 6).map((candidate) => (
            <div key={`guess-${candidate.key_guess}`} className="timeline-row">
              <span>Key {candidate.key_guess}</span>
              <span>Correlation {Number(candidate.correlation || 0).toFixed(3)}</span>
              <span>Type</span>
              <span>Power Analysis</span>
            </div>
          ))}
          {(attack.correlation_profile || []).length === 0 ? (
            <p className="muted">Attack profile is not available yet.</p>
          ) : null}
        </div>

        <h3 className="section-heading">Attack Event Log</h3>
        <div className="timeline-table">
          {(attackLog || []).slice(0, 6).map((entry, idx) => (
            <div key={`attack-log-${idx}-${entry}`} className="timeline-row attack-log-row">
              <span>Event</span>
              <span className="attack-log-text">{entry}</span>
              <span>Status</span>
              <span>{status.status === 'running' ? 'Running' : 'Stopped'}</span>
            </div>
          ))}
          {(attackLog || []).length === 0 ? <p className="muted">No attack events yet.</p> : null}
        </div>
      </section>

      <section className="panel tx-card">
        <h2>Recent Payment Decisions</h2>
        <div className="tx-list">
          {transactions.length === 0 ? (
            <p className="muted">No transactions yet. Initiate transfer to view decision flow.</p>
          ) : (
            transactions.map((tx) => (
              <article key={tx.id} className="tx-item">
                <div>
                  <strong>
                    INR {tx.amount} from {tx.senderName} to {tx.receiverName}
                  </strong>
                  <p>
                    {tx.senderPort} {'->'} {tx.receiverPort}
                    {tx.attackerEnabled ? ` (attacker ${tx.attackerPort})` : ''}
                  </p>
                  <p>{tx.note || 'No note'}</p>
                </div>
                <div className="tx-meta">
                  <span>{tx.time}</span>
                  <span className={`decision decision-${tx.decision.toLowerCase()}`}>{tx.decision}</span>
                  <span>Risk {(tx.risk * 100).toFixed(1)}%</span>
                  {tx.decision === 'THEFTED' ? <span>Theft INR {tx.theftAmount}</span> : null}
                  <button type="button" className="btn" onClick={() => onOpenReplay(tx)}>
                    View Replay
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      {scan.open ? (
        <div className="modal-backdrop" role="presentation">
          <section className="modal-card" role="dialog" aria-modal="true" aria-label="Live Risk Scan">
            <h2>Live Risk Scan</h2>
            <p>{scan.message}</p>
            <div className="progress-track soft">
              <div className="progress-fill" style={{ width: `${scan.progress}%` }}></div>
            </div>
            <p className="muted">Progress: {scan.progress}%</p>

            {scan.reasons?.length ? (
              <div className="reason-box">
                <p className="muted">Decision Breakdown</p>
                <ul>
                  {scan.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {scan.phase === 'otp' ? (
              <div className="otp-row">
                <label>
                  Enter OTP
                  <input
                    className="otp-input"
                    value={scan.otpInput}
                    onChange={(e) => onOtpChange(e.target.value)}
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={6}
                    placeholder="6-digit OTP"
                  />
                </label>
                {scan.otpError ? <p className="otp-error">{scan.otpError}</p> : null}
                <p className="muted">For demo, use OTP 123456.</p>
              </div>
            ) : null}

            {scan.phase === 'otp' ? (
              <div className="button-row">
                <button type="button" className="btn btn-primary" onClick={onOtpConfirm}>
                  Verify OTP
                </button>
                <button type="button" className="btn" onClick={closeModal}>
                  Cancel
                </button>
              </div>
            ) : null}

            {scan.phase === 'done' ? (
              <div className="button-row">
                <button type="button" className="btn" onClick={closeModal}>
                  Close
                </button>
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </main>
  )
}
