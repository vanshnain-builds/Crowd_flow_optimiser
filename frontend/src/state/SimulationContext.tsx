import type {
  Scenario, SimSnapshot, ConnectionState, AIProcessingStage,
  EmergencyEvent,
} from '@/types';
import {
  DEFAULT_SCENARIO, STADIUM_A,
} from '@/data/venue';
import {
  tick, resetSimulation, startSimulation, pauseSimulation,
  resumeSimulation, setSpeed, triggerEmergency, clearEmergency,
  interpretScenarioText, acknowledgeAlert, getLiveEdges, getLiveAgents,
} from '@/services/mockEngine';
import type { VenueEdge, SimAgent } from '@/types';
import {
  createContext, useContext, useEffect, useRef, useState, useCallback,
  type ReactNode,
} from 'react';
import {
  isBackendConfigured,
  createSimulationWebSocket,
  apiStart, apiPause, apiResume, apiReset, apiSetSpeed,
  apiTriggerEmergency, apiClearEmergency, apiParseScenario,
} from '@/services/backendClient';

// ===========================================================================
// Central real-time state layer
// Two modes:
//   1. BACKEND mode: WebSocket to FastAPI backend (VITE_BACKEND_URL set)
//   2. MOCK mode:   Local rAF tick loop (fallback, development default)
//
// All components use the same API regardless of mode.
// Components never open their own connections.
// ===========================================================================

const SIMULATION_ID = 'default';

interface SimulationApi {
  // state
  snapshot: SimSnapshot | null;
  connection: ConnectionState;
  scenario: Scenario;
  liveEdges: Record<string, VenueEdge>;
  liveAgents: SimAgent[];

  // simulation controls
  start: () => void;
  pause: () => void;
  resume: () => void;
  reset: () => void;
  setSpeedMult: (m: number) => void;

  // scenario
  setScenario: (s: Scenario) => void;
  interpretScenario: (text: string) => void;
  aiStage: AIProcessingStage;
  aiNotes: string[];
  aiExtracted: Partial<Scenario> | null;

  // emergency
  triggerEm: (type: EmergencyEvent['type'], nodeId: string) => void;
  clearEm: () => void;

  // alerts
  ackAlert: (id: string) => void;

  // map selection
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  selectNode: (id: string | null) => void;
  selectEdge: (id: string | null) => void;

  // map layer toggles
  layers: { crowd: boolean; density: boolean; bottlenecks: boolean; routes: boolean; heatmap: boolean };
  toggleLayer: (k: keyof SimulationApi['layers']) => void;
}

const Ctx = createContext<SimulationApi | null>(null);

const IDLE_SNAPSHOT_DELAY = 800;

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<SimSnapshot | null>(null);
  const [connection, setConnection] = useState<ConnectionState>('connecting');
  const [scenario, setScenarioState] = useState<Scenario>(DEFAULT_SCENARIO);
  const [aiStage, setAiStage] = useState<AIProcessingStage>('idle');
  const [aiNotes, setAiNotes] = useState<string[]>([]);
  const [aiExtracted, setAiExtracted] = useState<Partial<Scenario> | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [layers, setLayers] = useState({
    crowd: true,
    density: false,
    bottlenecks: true,
    routes: true,
    heatmap: false,
  });

  const scenarioRef = useRef(scenario);
  scenarioRef.current = scenario;
  const lastTickRef = useRef(performance.now());

  // ── Backend WebSocket mode ────────────────────────────────────────────────
  useEffect(() => {
    if (!isBackendConfigured) return; // use mock mode instead

    const cleanup = createSimulationWebSocket(
      SIMULATION_ID,
      (msg) => {
        const { type, payload } = msg as { type: string; payload: unknown };
        if (type === 'simulation.updated' && payload) {
          setSnapshot(payload as SimSnapshot);
        } else if (type === 'connection.status') {
          const { status } = payload as { status: string };
          if (status === 'live') setConnection('live');
        }
      },
      (status) => setConnection(status),
    );

    return cleanup;
  }, []);

  // ── Mock tick loop mode (when no backend configured) ──────────────────────
  useEffect(() => {
    if (isBackendConfigured) return; // backend mode active

    const t = setTimeout(() => setConnection('live'), IDLE_SNAPSHOT_DELAY);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (isBackendConfigured) return; // backend mode active

    let raf = 0;
    const loop = (now: number) => {
      const dt = Math.min(0.1, (now - lastTickRef.current) / 1000);
      lastTickRef.current = now;
      const snap = tick(scenarioRef.current, dt);
      setSnapshot(snap);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  // live edge/agent refs (read each render from engine — mock mode only)
  const liveEdges = isBackendConfigured ? (snapshot?.routing ? {} : getLiveEdges()) : getLiveEdges();
  const liveAgents = isBackendConfigured ? (snapshot?.simulation?.agents ?? []) : getLiveAgents();

  // ── Controls — dual mode ──────────────────────────────────────────────────

  const start = useCallback(() => {
    if (isBackendConfigured) {
      apiStart(SIMULATION_ID).catch(console.error);
    } else {
      startSimulation();
    }
  }, []);

  const pause = useCallback(() => {
    if (isBackendConfigured) {
      apiPause(SIMULATION_ID).catch(console.error);
    } else {
      pauseSimulation();
    }
  }, []);

  const resume = useCallback(() => {
    if (isBackendConfigured) {
      apiResume(SIMULATION_ID).catch(console.error);
    } else {
      resumeSimulation();
    }
  }, []);

  const reset = useCallback(() => {
    if (isBackendConfigured) {
      apiReset(SIMULATION_ID).catch(console.error);
      setSnapshot(null);
    } else {
      resetSimulation();
      setSnapshot(null);
    }
  }, []);

  const setSpeedMult = useCallback((m: number) => {
    if (isBackendConfigured) {
      apiSetSpeed(SIMULATION_ID, m).catch(console.error);
    } else {
      setSpeed(m);
    }
  }, []);

  const setScenario = useCallback((s: Scenario) => {
    setScenarioState(s);
    if (!isBackendConfigured) resetSimulation();
  }, []);

  // ── AI scenario interpretation ────────────────────────────────────────────

  const interpretScenario = useCallback((text: string) => {
    setAiStage('understanding');

    if (isBackendConfigured) {
      // Real AI backend call — show pipeline stages while waiting
      setTimeout(() => setAiStage('extracting'), 500);
      setTimeout(() => setAiStage('validating'), 1000);

      apiParseScenario(text)
        .then((result) => {
          if (result.success && result.parsed) {
            // Convert backend ParsedScenario to partial frontend Scenario
            const parsed = result.parsed as Record<string, unknown>;
            const extracted: Partial<Scenario> = {
              name: parsed.name as string,
              crowdSize: parsed.crowdSize as number,
              entryDistribution: parsed.entryDistribution as Scenario['entryDistribution'],
              timing: parsed.timing as Scenario['timing'],
            };
            setAiExtracted(extracted);
            setAiNotes(result.notes);
            setAiStage('ready');
          } else {
            setAiStage('idle');
          }
        })
        .catch(() => {
          // Fallback to mock interpretation
          const { extracted, notes } = interpretScenarioText(text);
          setAiExtracted(extracted);
          setAiNotes(notes);
          setAiStage('ready');
        });
    } else {
      // Mock mode — local interpretation
      setTimeout(() => setAiStage('extracting'), 500);
      setTimeout(() => {
        const { extracted, notes } = interpretScenarioText(text);
        setAiExtracted(extracted);
        setAiNotes(notes);
        setAiStage('validating');
      }, 1100);
      setTimeout(() => setAiStage('ready'), 1800);
    }
  }, []);

  // ── Emergency ─────────────────────────────────────────────────────────────

  const triggerEm = useCallback(
    (type: EmergencyEvent['type'], nodeId: string) => {
      if (isBackendConfigured) {
        apiTriggerEmergency(SIMULATION_ID, type, nodeId).catch(console.error);
      } else {
        triggerEmergency(type, nodeId);
      }
    },
    [],
  );

  const clearEm = useCallback(() => {
    if (isBackendConfigured) {
      apiClearEmergency(SIMULATION_ID).catch(console.error);
    } else {
      clearEmergency();
    }
  }, []);

  const ackAlert = useCallback((id: string) => {
    acknowledgeAlert(id);
  }, []);

  // ── Map selection ─────────────────────────────────────────────────────────

  const selectNode = useCallback((id: string | null) => {
    setSelectedNodeId(id);
    setSelectedEdgeId(null);
  }, []);

  const selectEdge = useCallback((id: string | null) => {
    setSelectedEdgeId(id);
    setSelectedNodeId(null);
  }, []);

  const toggleLayer = useCallback((k: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [k]: !prev[k] }));
  }, []);

  const api: SimulationApi = {
    snapshot, connection, scenario, liveEdges, liveAgents,
    start, pause, resume, reset, setSpeedMult,
    setScenario, interpretScenario, aiStage, aiNotes, aiExtracted,
    triggerEm, clearEm, ackAlert,
    selectedNodeId, selectedEdgeId, selectNode, selectEdge,
    layers, toggleLayer,
  };

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function useSimulation(): SimulationApi {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider');
  return ctx;
}

export { STADIUM_A };
