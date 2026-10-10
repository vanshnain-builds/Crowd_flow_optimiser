import { useSimulation } from '@/state/SimulationContext';
import { riskColor, riskLabel, pct, formatCountdown } from '@/utils/display';
import { Flame, Crosshair, TrendingUp, CheckCircle2 } from 'lucide-react';

export function BottleneckPanel() {
  const { snapshot, selectEdge } = useSimulation();
  const bottlenecks = snapshot?.safety.bottlenecks ?? [];
  const predicted = snapshot?.safety.predictedBottlenecks ?? [];

  if (bottlenecks.length === 0 && predicted.length === 0) {
    return (
      <div className="cmd-panel rounded-lg p-3">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle2 size={14} color="#8fa66f" />
          <span className="cmd-label">Bottlenecks</span>
          <span className="status-badge status-badge--safe ml-auto">CLEAR</span>
        </div>
        <div className="empty-state empty-state--small">
          <div className="empty-state__icon"><Flame size={14} /></div>
          <div>
            <div className="empty-state__title">All corridors clear</div>
            <div className="empty-state__copy">No current or predicted capacity constraint.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cmd-panel rounded-lg overflow-hidden">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Flame size={14} color="#d7a24a" />
          <span className="cmd-label">Bottlenecks</span>
        </div>
        <span className="panel-count">{bottlenecks.length} active · {predicted.length} predicted</span>
      </div>
      <div className="max-h-[210px] overflow-y-auto">
        {bottlenecks.map((b) => (
          <BottleneckRow key={b.id} b={b} predicted={false} onClick={() => selectEdge(b.edgeId)} />
        ))}
        {predicted.map((b) => (
          <BottleneckRow key={b.id} b={b} predicted={true} onClick={() => selectEdge(b.edgeId)} />
        ))}
      </div>
    </div>
  );
}

function BottleneckRow({ b, predicted, onClick }: {
  b: import('@/types').Bottleneck; predicted: boolean; onClick: () => void;
}) {
  const color = riskColor(b.risk);
  return (
    <button onClick={onClick}
      className="w-full text-left px-3 py-2 border-b border-[var(--cmd-border)] hover:bg-[var(--cmd-surface-2)] transition-colors flex items-start gap-2.5">
      <div className="mt-0.5 flex-shrink-0">
        {predicted ? <TrendingUp size={14} color="#d7a24a" /> : <Flame size={14} style={{ color }} />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[12px] font-semibold text-white truncate">{b.location}</span>
          {predicted && <span className="status-badge status-badge--warning">PREDICTED</span>}
          <span className="ml-auto text-[8px] font-bold px-1.5 py-0.5 rounded"
            style={{ background: color + '22', color }}>
            {riskLabel(b.risk).toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px]" style={{ color: 'var(--cmd-text-dim)' }}>
          <span>Util <span className="cmd-mono-value" style={{ color }}>{pct(b.capacityUtilization)}</span></span>
          {b.timeToCriticalMin != null && (
            <span>TTC <span className="cmd-mono-value" style={{ color: b.timeToCriticalMin < 10 ? '#d85b52' : '#d7a24a' }}>{formatCountdown(b.timeToCriticalMin)}</span></span>
          )}
        </div>
        <div className="text-[10px] mt-1" style={{ color: 'var(--cmd-text-dim)' }}>{b.recommendedAction}</div>
      </div>
      <Crosshair size={12} className="mt-1 flex-shrink-0" style={{ color: 'var(--cmd-text-faint)' }} />
    </button>
  );
}
