import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Dashboard from './Dashboard'
import { SimulationContext } from '../context/simulationContextObject'

const contextValue = {
  config: { algorithm: 'AES', attack_type: 'power', runs: 1000, enable_ai: true, auto_defense: true },
  setConfig: () => {},
  status: { status: 'running', runs_completed: 240, total_runs: 1000 },
  metrics: {
    execution_time_ms: 2.3,
    cpu_usage_pct: 17.9,
    memory_usage_mb: 14.4,
    clock_cycles: 7340,
    power_avg: 33.8,
    power_peak: 40.2,
    hamming_weight_mean: 12.2,
    hamming_distance_mean: 9.1,
    leakage_score: 0.84,
    correlation_score: 0.91,
    cache_hits: 312,
    cache_misses: 18,
    cache_miss_rate: 5.4,
    power_trace: [30, 34, 36, 33],
  },
  history: {
    run: [1, 2, 3],
    power: [31, 33, 34],
    timing: [2.1, 2.2, 2.3],
    correlation: [0.62, 0.71, 0.91],
  },
  attack: {
    keys_tested: 120,
    best_key_guess: '3A',
    correlation: 0.91,
    attack_progress: 45,
    correlation_profile: [{ key_guess: '3A', correlation: 0.91 }],
  },
  attackLog: ['[12:00:00] Auto-defense activated with masking.'],
  ai: { attack_probability: 0.78, risk_level: 'HIGH', model_confidence: 0.91, top_features: [] },
  defense: {
    defense_mode: 'ACTIVE',
    technique: 'masking',
    security_level: 'HIGH',
    leakage_reduction: 0.42,
  },
  socketState: 'connected',
  loading: false,
  error: '',
  refreshSnapshot: () => {},
  onStart: () => {},
  onStop: () => {},
  onReset: () => {},
  onActivateDefense: () => {},
  onDisableDefense: () => {},
  onTrainAI: () => {},
  onExportDataset: () => {},
}

describe('Dashboard', () => {
  it('renders the main simulator panels', () => {
    render(
      <SimulationContext.Provider value={contextValue}>
        <Dashboard />
      </SimulationContext.Provider>,
    )

    expect(screen.getByText(/Control Panel/i)).toBeInTheDocument()
    expect(screen.getByText(/Defense Panel/i)).toBeInTheDocument()
    expect(screen.getByText(/Attack Log/i)).toBeInTheDocument()
    expect(screen.getByText('3A')).toBeInTheDocument()
  })
})
