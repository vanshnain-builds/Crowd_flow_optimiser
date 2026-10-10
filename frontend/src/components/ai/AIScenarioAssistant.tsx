import { useState } from 'react';
import { useSimulation } from '@/state/SimulationContext';
import { Sparkles, Loader2, CheckCircle2, ChevronRight, Edit3 } from 'lucide-react';
import type { AIProcessingStage } from '@/types';

const SAMPLE = `A concert with 20,000 people starts at 7 PM. Most people enter through the east gate and food stalls are near the north corridor.`;

export function AIScenarioAssistant() {
  const { interpretScenario, aiStage, aiNotes, aiExtracted, scenario } = useSimulation();
  const [text, setText] = useState('');

  const stageLabel: Record<AIProcessingStage, string> = {
    idle: 'Idle',
    understanding: 'Understanding scenario…',
    extracting: 'Extracting parameters…',
    validating: 'Validating scenario…',
    ready: 'Scenario ready',
    analyzing: 'Analyzing…',
    complete: 'Complete',
  };

  const isProcessing = aiStage === 'understanding' || aiStage === 'extracting' || aiStage === 'validating';
  const isReady = aiStage === 'ready' && aiExtracted;

  return (
    <div className="cmd-panel rounded p-3 space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles size={14} style={{ color: '#d39a5a' }} />
        <span className="cmd-label">AI Scenario Assistant</span>
      </div>

      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe your event in natural language…"
          rows={3}
          className="w-full bg-[var(--cmd-bg)] border border-[var(--cmd-border)] rounded p-2.5 text-[12px] text-[var(--cmd-text)] placeholder:text-[var(--cmd-text-faint)] resize-none focus:outline-none focus:border-[var(--live)] focus:ring-1 focus:ring-[var(--live)]/30 transition-colors"
        />
      </div>

      <div className="flex items-center gap-2">
        <button onClick={() => text.trim() && interpretScenario(text)}
          disabled={!text.trim() || isProcessing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] font-semibold transition-all disabled:opacity-40"
          style={{ background: 'rgba(211,154,90,0.10)', border: '1px solid rgba(211,154,90,0.55)', color: '#d39a5a' }}>
          {isProcessing ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
          <span>{isProcessing ? 'PROCESSING' : 'INTERPRET'}</span>
        </button>
        <button onClick={() => setText(SAMPLE)}
          className="text-[10px] text-[var(--cmd-text-dim)] hover:text-[var(--cmd-text)] underline underline-offset-2">
          Use sample
        </button>
      </div>

      {/* processing pipeline */}
      {aiStage !== 'idle' && (
        <div className="space-y-1.5 pt-1">
          <PipelineStage active={aiStage === 'understanding'} done={aiStage === 'extracting' || aiStage === 'validating' || aiStage === 'ready'} label="Understanding scenario" />
          <PipelineStage active={aiStage === 'extracting'} done={aiStage === 'validating' || aiStage === 'ready'} label="Extracting parameters" />
          <PipelineStage active={aiStage === 'validating'} done={aiStage === 'ready'} label="Validating scenario" />
          {isReady && <PipelineStage active={false} done={true} label="Scenario ready" />}
        </div>
      )}

      {/* extracted parameters */}
      {isReady && aiExtracted && (
        <div className="space-y-2 pt-2 border-t border-[var(--cmd-border)]">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 size={12} color="#8fa66f" />
            <span className="cmd-label">Extracted Parameters</span>
            <span className="ml-auto text-[9px] text-[var(--cmd-text-faint)] flex items-center gap-1">
              <Edit3 size={9} /> Editable
            </span>
          </div>
          {aiNotes.map((n, i) => (
            <div key={i} className="flex items-center gap-1.5 text-[11px]" style={{ color: 'var(--cmd-text-dim)' }}>
              <ChevronRight size={11} color="#d39a5a" />
              <span>{n}</span>
            </div>
          ))}
          <div className="grid grid-cols-2 gap-1.5 pt-1">
            {aiExtracted.crowdSize != null && (
              <ParamRow label="Crowd Size" value={aiExtracted.crowdSize.toLocaleString()} />
            )}
            {aiExtracted.timing && (
              <ParamRow label="Event Start"
                value={`${String(Math.floor(aiExtracted.timing.startMinutesOfDay / 60)).padStart(2, '0')}:00`} />
            )}
            {aiExtracted.entryDistribution && (
              <ParamRow label="Primary Entry"
                value={aiExtracted.entryDistribution[0]
                  ? gateLabel(aiExtracted.entryDistribution[0].gateId) : '—'} />
            )}
            {aiExtracted.name && (
              <ParamRow label="Event Type" value={aiExtracted.name} />
            )}
          </div>
          <div className="text-[10px] text-[var(--cmd-text-faint)] pt-1">
            Current scenario: <span className="text-[var(--cmd-text-dim)]">{scenario.name}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function gateLabel(id: string): string {
  const map: Record<string, string> = {
    'gate-e': 'East Gate', 'gate-w': 'West Gate', 'gate-s': 'South Gate',
  };
  return map[id] ?? id;
}

function PipelineStage({ active, done, label }: {
  active: boolean; done: boolean; label: string;
}) {
  return (
    <div className="flex items-center gap-2 text-[11px]">
      {done ? <CheckCircle2 size={12} color="#8fa66f" />
        : active ? <Loader2 size={12} className="animate-spin" color="#d39a5a" />
        : <div className="w-3 h-3 rounded-full border border-[var(--cmd-border-bright)]" />}
      <span style={{ color: done ? '#8fa66f' : active ? '#d39a5a' : 'var(--cmd-text-faint)' }}>
        {label}
      </span>
    </div>
  );
}

function ParamRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="cmd-surface-2 rounded px-2 py-1.5">
      <div className="cmd-label text-[9px]">{label}</div>
      <div className="text-[12px] font-semibold text-white">{value}</div>
    </div>
  );
}
