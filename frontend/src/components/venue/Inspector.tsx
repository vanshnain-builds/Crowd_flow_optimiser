import { useSimulation } from '@/state/SimulationContext';
import { NODE_MAP, EDGE_MAP } from '@/data/venue';
import { nodeKindColor } from '@/utils/venueColors';
import { pct, formatCountdown } from '@/utils/display';
import { X, MapPin, ArrowRight, Users, Gauge, AlertTriangle, Route, Crosshair } from 'lucide-react';

export function Inspector() {
  const { snapshot, selectedNodeId, selectedEdgeId, selectNode, selectEdge, liveEdges } = useSimulation();
  if (!selectedNodeId && !selectedEdgeId) return null;

  const close = () => { selectNode(null); selectEdge(null); };

  return (
    <div className="inspector absolute top-3 right-3 w-[260px] cmd-surface rounded-lg shadow-2xl z-20 pointer-events-auto">
      <div className="inspector__header">
        <div className="flex items-center gap-2">
          <Crosshair size={12} color="#d39a5a" />
          <div>
            <div className="cmd-label">Selected on map</div>
            <div className="text-[10px]" style={{ color: 'var(--cmd-text-dim)' }}>Inspector</div>
          </div>
        </div>
        <button onClick={close} className="icon-button" aria-label="Close inspector"><X size={13} /></button>
      </div>
      {selectedNodeId && <NodeInspector nodeId={selectedNodeId} />}
      {selectedEdgeId && <EdgeInspector edgeId={selectedEdgeId} liveDensity={liveEdges[selectedEdgeId]?.density ?? 0} />}
    </div>
  );
}

function NodeInspector({ nodeId }: { nodeId: string }) {
  const { snapshot, liveAgents } = useSimulation();
  const node = NODE_MAP[nodeId];
  if (!node) return null;
  const color = nodeKindColor(node.kind);
  const agentsHere = liveAgents.filter((a) => a.fromNodeId === nodeId).length;
  const bn = snapshot?.safety.bottlenecks.find((b) => b.edgeId && EDGE_MAP[b.edgeId]?.to === nodeId);
  const occupancy = node.capacity ? Math.min(1, agentsHere / node.capacity) : 0;

  return (
    <div className="p-3 space-y-2.5">
      <div className="flex items-center gap-2">
        <MapPin size={15} style={{ color }} />
        <div>
          <div className="text-[13px] font-bold text-white">{node.label}</div>
          <div className="text-[10px] capitalize" style={{ color: 'var(--cmd-text-dim)' }}>{node.kind} · selected</div>
        </div>
      </div>
      {node.description && <div className="text-[10px] leading-relaxed" style={{ color: 'var(--cmd-text-dim)' }}>{node.description}</div>}
      <div className="occupancy-block">
        <div className="flex items-center justify-between text-[9px] mb-1">
          <span className="cmd-label text-[8px]">Occupancy</span>
          <span className="cmd-mono-value text-white">{pct(occupancy)} of {node.capacity.toLocaleString()}</span>
        </div>
        <div className="occupancy-bar"><span style={{ width: `${occupancy * 100}%`, background: occupancy > .8 ? '#d85b52' : '#d39a5a' }} /></div>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        <Info label="Capacity" value={node.capacity.toLocaleString()} />
        <Info label="Agents" value={String(agentsHere)} icon={<Users size={10} />} />
      </div>
      {bn && (
        <div className="critical-card">
          <div className="flex items-center gap-1.5 mb-1"><AlertTriangle size={11} color="#d85b52" /><span className="text-[10px] font-bold text-[#d85b52]">BOTTLENECK</span></div>
          <Info label="Utilization" value={pct(bn.capacityUtilization)} />
          {bn.timeToCriticalMin != null && <Info label="Time to Critical" value={formatCountdown(bn.timeToCriticalMin)} />}
        </div>
      )}
    </div>
  );
}

function EdgeInspector({ edgeId, liveDensity }: { edgeId: string; liveDensity: number }) {
  const { snapshot } = useSimulation();
  const edge = EDGE_MAP[edgeId];
  if (!edge) return null;
  const from = NODE_MAP[edge.from], to = NODE_MAP[edge.to];
  const isDisabled = snapshot?.routing.disabledEdges.includes(edgeId) ?? false;
  const bn = snapshot?.safety.bottlenecks.find((b) => b.edgeId === edgeId);
  const color = isDisabled ? '#e04d45' : liveDensity > 0.7 ? '#d85b52' : liveDensity > 0.4 ? '#d7a24a' : '#b5a994';

  return (
    <div className="p-3 space-y-2.5">
      <div className="flex items-center gap-2">
        <Route size={15} style={{ color }} />
        <div>
          <div className="text-[12px] font-semibold text-white flex items-center gap-1.5">{from?.label} <ArrowRight size={11} /> {to?.label}</div>
          <div className="text-[10px]" style={{ color: 'var(--cmd-text-dim)' }}>Corridor · selected</div>
        </div>
      </div>
      <div className="occupancy-block">
        <div className="flex items-center justify-between text-[9px] mb-1"><span className="cmd-label text-[8px]">Live density</span><span className="cmd-mono-value" style={{ color }}>{pct(liveDensity)}</span></div>
        <div className="occupancy-bar"><span style={{ width: `${Math.min(1, liveDensity) * 100}%`, background: color }} /></div>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        <Info label="Width" value={`${edge.width}m`} />
        <Info label="Length" value={`${edge.length}m`} />
        <Info label="Capacity" value={`${edge.capacity}/min`} />
        <Info label="Cost" value={edge.cost.toFixed(1)} />
        <Info label="Flow" value={`${edge.flow}/min`} icon={<Gauge size={10} />} />
        <Info label="Density" value={pct(liveDensity)} color={color} />
      </div>
      {isDisabled && <div className="critical-card flex items-center gap-1.5"><AlertTriangle size={11} color="#e04d45" /><span className="text-[10px] font-bold text-[#e04d45]">ROUTE DISABLED</span></div>}
      {bn && <div className="text-[10px] leading-relaxed" style={{ color: 'var(--cmd-text-dim)' }}>{bn.recommendedAction}</div>}
    </div>
  );
}

function Info({ label, value, color, icon }: { label: string; value: string; color?: string; icon?: React.ReactNode }) {
  return (
    <div className="cmd-surface-2 rounded px-2 py-1.5">
      <div className="cmd-label text-[8px] flex items-center gap-1">{icon}{label}</div>
      <div className="text-[12px] font-semibold cmd-mono-value" style={{ color: color ?? '#fff' }}>{value}</div>
    </div>
  );
}
