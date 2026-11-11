from typing import Any, Dict, List
from app.models.files import GeneratedFile


class InterfaceGenerator:
    """Generates React Dashboard / Web App interface strictly bound to declared
    metrics and behavioral commands.
    """

    @classmethod
    def generate(cls, project_id: str, version: int, spec: Dict[str, Any]) -> List[GeneratedFile]:
        files: List[GeneratedFile] = []

        interface = spec.get("interface", {}).get("fields", {})
        data_model = spec.get("data_model", {}).get("fields", {})
        behavior = spec.get("behavior", {}).get("fields", {})

        interface_type = str(interface.get("interface_type", {}).get("value") or "dashboard")
        metrics: List[Dict[str, Any]] = data_model.get("metrics", {}).get("value") or []
        declared_cmds: List[str] = behavior.get("declared_commands", {}).get("value") or []

        component_code = f"""import React, {{ useState, useEffect }} from 'react';

/* USER CODE BEGIN CUSTOM_IMPORTS */
// Import custom charts or icons
/* USER CODE END CUSTOM_IMPORTS */

export default function NodeInterface() {{
  const [telemetry, setTelemetry] = useState({{
    temperature_c: 24.8,
    relative_humidity_pct: 58.2,
    barometric_pressure_hpa: 1012.4,
    battery_voltage_v: 3.92,
  }});
  const [commandStatus, setCommandStatus] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSendCommand = async (cmd) => {{
    setIsSubmitting(true);
    setCommandStatus(`Sending ${{cmd}}...`);
    try {{
      const res = await fetch('/api/commands/dispatch', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ command: cmd }}),
      }});
      if (res.ok) {{
        setCommandStatus(`Command ${{cmd}} dispatched successfully!`);
      }} else {{
        setCommandStatus(`Failed to dispatch command: ${{res.statusText}}`);
      }}
    }} catch (err) {{
      setCommandStatus(`Error: ${{err.message}}`);
    }} finally {{
      setIsSubmitting(false);
    }}
  }};

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 font-sans">
      <div className="border-b pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Node Telemetry & Controls</h1>
          <p className="text-xs text-gray-500">Interface Mode: {interface_type.upper()} | Spec v{version}.0</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-semibold text-emerald-600">Live Telemetry</span>
        </div>
      </div>

      {{/* Telemetry Metric Cards */}}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
"""
        for m in metrics:
            m_name = m.get("name", "metric")
            m_unit = m.get("unit", "")
            component_code += f"""        <div className="p-4 rounded-xl border bg-white shadow-xs">
          <div className="text-xs text-gray-400 capitalize">{m_name.replace('_', ' ')}</div>
          <div className="text-2xl font-bold mt-1 text-gray-800">
            {{telemetry.{m_name} ?? '--'}} <span className="text-xs font-normal text-gray-500">{m_unit}</span>
          </div>
        </div>
"""

        component_code += f"""      </div>

      {{/* Actuator Controls (Mapped to Behavior Declared Commands) */}}
      <div className="p-5 rounded-xl border bg-gray-50 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Hardware Actuator Commands</h3>
        <div className="flex flex-wrap gap-2.5">
"""
        for cmd in declared_cmds:
            component_code += f"""          <button
            onClick={{() => handleSendCommand('{cmd}')}}
            disabled={{isSubmitting}}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
          >
            {cmd.replace('_', ' ')}
          </button>
"""

        component_code += """        </div>
        {commandStatus && (
          <div className="text-xs font-mono text-gray-600 pt-1">
            Status: {commandStatus}
          </div>
        )}
      </div>

      /* USER CODE BEGIN CUSTOM_WIDGETS */
      {/* Add custom analytics widgets or data tables below */}
      /* USER CODE END CUSTOM_WIDGETS */
    </div>
  );
}
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-interface-app",
                project_id=project_id,
                version_number=version,
                path="interface/src/App.jsx",
                content=component_code,
                file_type="interface",
            )
        )

        return files
