/* eslint-disable react-refresh/only-export-components */
import { useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  activateDefense,
  disableDefense,
  exportDataset,
  getAttackLog,
  getAttackStatus,
  getAIPrediction,
  getCurrentMetrics,
  getDefenseStatus,
  getMetricsHistory,
  getSimulationStatus,
  resetSimulation,
  startAttack,
  startSimulation,
  stopSimulation,
  trainAI,
} from '../services/api'
import { useMetrics } from '../hooks/useMetrics'
import { SimulationContext } from './simulationContextObject'

const HISTORY_LIMIT = 80

const DEFAULT_CONFIG = {
  algorithm: 'AES',
  attack_type: 'power',
  runs: 1000,
  enable_ai: true,
  auto_defense: true,
}

const DEFAULT_STATUS = {
  status: 'idle',
  algorithm: 'AES',
  attack_type: 'power',
  runs_completed: 0,
  total_runs: 1000,
}

const DEFAULT_METRICS = {
  execution_time_ms: 0,
  cpu_usage_pct: 0,
  memory_usage_mb: 0,
  clock_cycles: 0,
  power_avg: 0,
  power_peak: 0,
  power_variance: 0,
  hamming_weight_mean: 0,
  hamming_distance_mean: 0,
  leakage_score: 0,
  correlation_score: 0,
  cache_hits: 0,
  cache_misses: 0,
  cache_miss_rate: 0,
  power_trace: [],
}

function mapHistory(records) {
  const sliced = records.slice(Math.max(records.length - HISTORY_LIMIT, 0))
  return {
    run: sliced.map((record) => record.run_index),
    power: sliced.map((record) => record.power_avg),
    timing: sliced.map((record) => record.execution_time_ms),
    correlation: sliced.map((record) => record.correlation_score),
  }
}

function downloadBlob(blob, fileName) {
  const objectUrl = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = fileName
  anchor.click()
  window.URL.revokeObjectURL(objectUrl)
}

export function SimulationProvider({ children }) {
  const [config, setConfig] = useState(DEFAULT_CONFIG)
  const [status, setStatus] = useState(DEFAULT_STATUS)
  const [metrics, setMetrics] = useState(DEFAULT_METRICS)
  const [history, setHistory] = useState({ run: [], power: [], timing: [], correlation: [] })
  const [attack, setAttack] = useState({
    keys_tested: 0,
    best_key_guess: '--',
    correlation: 0,
    attack_progress: 0,
    correlation_profile: [],
  })
  const [attackLog, setAttackLog] = useState([])
  const [ai, setAi] = useState({
    attack_probability: 0,
    risk_level: 'LOW',
    model_confidence: 0,
    top_features: [],
  })
  const [defense, setDefense] = useState({
    defense_mode: 'INACTIVE',
    technique: 'none',
    security_level: 'MEDIUM',
    leakage_reduction: 0,
  })
  const [socketState, setSocketState] = useState('disconnected')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const mergeFrame = useCallback((frame) => {
    if (frame.simulation) {
      setStatus((prev) => ({ ...prev, ...frame.simulation }))
    }
    if (frame.current) {
      setMetrics((prev) => ({ ...prev, ...frame.current }))
    }
    if (frame.attack) {
      setAttack((prev) => ({ ...prev, ...frame.attack }))
    }
    if (frame.ai) {
      setAi((prev) => ({ ...prev, ...frame.ai }))
    }
    if (frame.defense) {
      setDefense((prev) => ({ ...prev, ...frame.defense }))
    }
    if (Array.isArray(frame.history)) {
      setHistory(mapHistory(frame.history))
    }
    if (Array.isArray(frame.logs)) {
      setAttackLog(frame.logs.slice(0, 25))
    }
  }, [])

  useMetrics({
    enabled: status.status === 'running',
    onFrame: mergeFrame,
    onSocketState: setSocketState,
  })

  const refreshSnapshot = useCallback(async () => {
    try {
      const [statusData, metricsData, historyData, attackData, aiData, defenseData, logsData] =
        await Promise.all([
          getSimulationStatus(),
          getCurrentMetrics(),
          getMetricsHistory(HISTORY_LIMIT),
          getAttackStatus(),
          getAIPrediction(),
          getDefenseStatus(),
          getAttackLog(),
        ])

      setStatus((prev) => ({ ...prev, ...statusData }))
      setMetrics((prev) => ({ ...prev, ...metricsData }))
      setHistory(mapHistory(historyData))
      setAttack((prev) => ({ ...prev, ...attackData }))
      setAi((prev) => ({ ...prev, ...aiData }))
      setDefense((prev) => ({ ...prev, ...defenseData }))
      if (Array.isArray(logsData)) {
        setAttackLog(logsData.slice(0, 25))
      }
      setError('')
    } catch (snapshotError) {
      setError(snapshotError?.message || 'Unable to refresh simulator data')
    }
  }, [])

  useEffect(() => {
    refreshSnapshot()
  }, [refreshSnapshot])

  const onStart = useCallback(async () => {
    setLoading(true)
    try {
      await startSimulation(config)
      await startAttack()
      setStatus((prev) => ({ ...prev, status: 'running', total_runs: config.runs }))
      setError('')
      await refreshSnapshot()
    } catch (startError) {
      setError(startError?.message || 'Failed to start simulation')
    } finally {
      setLoading(false)
    }
  }, [config, refreshSnapshot])

  const onStop = useCallback(async () => {
    setLoading(true)
    try {
      await stopSimulation()
      setStatus((prev) => ({ ...prev, status: 'stopped' }))
      setError('')
      await refreshSnapshot()
    } catch (stopError) {
      setError(stopError?.message || 'Failed to stop simulation')
    } finally {
      setLoading(false)
    }
  }, [refreshSnapshot])

  const onReset = useCallback(async () => {
    setLoading(true)
    try {
      await resetSimulation()
      setStatus({ ...DEFAULT_STATUS, total_runs: config.runs })
      setMetrics(DEFAULT_METRICS)
      setHistory({ run: [], power: [], timing: [], correlation: [] })
      setAttack({
        keys_tested: 0,
        best_key_guess: '--',
        correlation: 0,
        attack_progress: 0,
        correlation_profile: [],
      })
      setAi({
        attack_probability: 0,
        risk_level: 'LOW',
        model_confidence: 0,
        top_features: [],
      })
      setDefense({
        defense_mode: 'INACTIVE',
        technique: 'none',
        security_level: 'MEDIUM',
        leakage_reduction: 0,
      })
      setAttackLog([])
      setError('')
    } catch (resetError) {
      setError(resetError?.message || 'Failed to reset simulation')
    } finally {
      setLoading(false)
    }
  }, [config.runs])

  const onActivateDefense = useCallback(async (technique) => {
    try {
      await activateDefense(technique)
      await refreshSnapshot()
    } catch (defenseError) {
      setError(defenseError?.message || 'Failed to activate defense')
    }
  }, [refreshSnapshot])

  const onDisableDefense = useCallback(async () => {
    try {
      await disableDefense()
      await refreshSnapshot()
    } catch (defenseError) {
      setError(defenseError?.message || 'Failed to disable defense')
    }
  }, [refreshSnapshot])

  const onTrainAI = useCallback(async () => {
    setLoading(true)
    try {
      await trainAI()
      await refreshSnapshot()
      setError('')
    } catch (aiError) {
      setError(aiError?.message || 'Failed to train AI model')
    } finally {
      setLoading(false)
    }
  }, [refreshSnapshot])

  const onExportDataset = useCallback(async () => {
    try {
      const blob = await exportDataset()
      downloadBlob(blob, 'side_channel_dataset.csv')
      setError('')
    } catch (exportError) {
      setError(exportError?.message || 'Failed to export dataset')
    }
  }, [])

  const value = useMemo(
    () => ({
      config,
      setConfig,
      status,
      metrics,
      history,
      attack,
      attackLog,
      ai,
      defense,
      socketState,
      loading,
      error,
      refreshSnapshot,
      onStart,
      onStop,
      onReset,
      onActivateDefense,
      onDisableDefense,
      onTrainAI,
      onExportDataset,
    }),
    [
      config,
      status,
      metrics,
      history,
      attack,
      attackLog,
      ai,
      defense,
      socketState,
      loading,
      error,
      refreshSnapshot,
      onStart,
      onStop,
      onReset,
      onActivateDefense,
      onDisableDefense,
      onTrainAI,
      onExportDataset,
    ],
  )

  return <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>
}

export function useSimulation() {
  const context = useContext(SimulationContext)
  if (!context) {
    throw new Error('useSimulation must be used within SimulationProvider')
  }
  return context
}
