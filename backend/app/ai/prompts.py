from __future__ import annotations

"""
Prompt templates for AI calls.
These are NOT hardcoded in the provider implementations.
"""

SCENARIO_SYSTEM_PROMPT = """You are a crowd safety simulation expert assistant.
Your task is to extract structured parameters from a natural language event description.
You must output ONLY valid JSON conforming exactly to the schema provided.
Do NOT invent values that are not mentioned in the user's description.
If a value is not mentioned, use the default.
Do not include explanatory text outside the JSON object.
"""

SCENARIO_USER_PROMPT_TEMPLATE = """Extract crowd simulation parameters from this event description:

"{text}"

Available venue nodes (valid IDs for gates and destinations):
- Entry gates: gate-w (West Gate), gate-e (East Gate), gate-s (South Gate)
- Exits: exit-n (North Exit), exit-sw (SW Exit), exit-se (SE Exit)
- Destinations: stage (Main Stage), food-n (North Food Court), food-s (South Food Court), medical (Medical Station)
- Junctions: j-w, j-e, j-n, j-s, j-nw, j-ne, j-sw, j-se

Output a JSON object with this exact schema:
{{
  "name": "Event name (string)",
  "crowdSize": <number, required>,
  "timing": {{
    "startMinutesOfDay": <minutes 0-1439, e.g. 19*60=1140 for 7 PM>,
    "durationMin": <minutes, default 180>,
    "arrivalPattern": "surge|gradual|sustained|peak-early",
    "departurePattern": "surge|gradual|sustained"
  }},
  "entryDistribution": [
    {{"gateId": "gate-e|gate-w|gate-s", "fraction": <0.0-1.0>}}
  ],
  "crowdGroups": [
    {{
      "id": "g-1",
      "name": "Group name",
      "size": <number>,
      "entryGateId": "gate-e|gate-w|gate-s",
      "destinationNodeId": "stage|food-n|food-s|exit-n|exit-sw|exit-se",
      "arrivalStartMin": <minutes from event start, e.g. -60>,
      "arrivalEndMin": <minutes from event start, e.g. 0>
    }}
  ],
  "entryRate": <people per minute, default 500>,
  "exitRate": <people per minute, default 800>,
  "notes": ["note about what was inferred", ...]
}}

Rules:
- crowdSize is REQUIRED and must be a positive number
- If entry gates are not specified, split equally across gate-e and gate-w
- If destinations are not specified, default to "stage"
- fractions in entryDistribution must sum to 1.0
- Do not invent crowd sizes or times that are not stated
- notes array should list what parameters were extracted vs defaulted"""


SAFETY_SYSTEM_PROMPT = """You are a crowd safety analyst for a live event venue management system.
You are given real-time simulation data. Your job is to:
1. Explain the current safety situation in clear, professional language
2. Identify the most critical risks based on the data provided
3. Recommend specific actionable interventions for venue operators
4. NOT calculate any numbers — only interpret the numbers provided

Output ONLY valid JSON conforming to the schema. No explanatory text outside JSON.
"""

SAFETY_USER_PROMPT_TEMPLATE = """Analyze this real-time crowd simulation data and provide a safety assessment:

SIMULATION STATUS:
- Time: {sim_time_min:.1f} min from event start
- Active crowd: {people_count:,} people
- Crowd status: {sim_status}

CROWD METRICS:
- Average density: {avg_density:.1%}
- Flow rate: {flow_rate:.0f} people/min
- Average speed: {avg_speed:.2f} units/s
- Capacity utilization: {capacity_utilization:.1%}
- Queue growth: {queue_growth:.2f} people/min

RISK ASSESSMENT:
- Risk score: {risk_score}/100
- Risk level: {risk_level}
- Time to critical: {ttc}

ACTIVE BOTTLENECKS ({bn_count}):
{bottleneck_details}

EMERGENCY: {emergency_status}

RECENT ROUTE CHANGES: {route_changes}

Based on this data, output a JSON object:
{{
  "summary": "One sentence summary of the current situation",
  "risk_explanation": "2-3 sentences explaining WHY the risk level is what it is, based on the metrics",
  "affected_locations": ["list", "of", "location", "names", "from", "the", "data"],
  "contributing_factors": ["factor1", "factor2", ...],
  "recommended_action": "Specific, actionable recommendation for venue operators",
  "urgency": "low|moderate|high|critical|emergency",
  "supporting_metrics": {{
    "key_metric_name": <value from the data above>
  }},
  "confidence": "low|medium|high"
}}

CRITICAL: Use ONLY the numbers provided above. Do not calculate, estimate, or invent new numbers."""
