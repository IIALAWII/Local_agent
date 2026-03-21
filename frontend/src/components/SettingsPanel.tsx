'use client';

import { X } from 'lucide-react';

interface AgentSettings {
  model: string;
  temperature: number;
  useAgent: boolean;
  stream: boolean;
}

interface SettingsPanelProps {
  settings: AgentSettings;
  onChange: (settings: AgentSettings) => void;
  onClose: () => void;
}

/**
 * Slide-in settings panel for controlling the model, temperature, and feature flags.
 */
export function SettingsPanel({ settings, onChange, onClose }: SettingsPanelProps) {
  const update = (partial: Partial<AgentSettings>) =>
    onChange({ ...settings, ...partial });

  return (
    <div className="border-b border-gray-800 bg-gray-900 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-white">Settings</h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-300 transition-colors"
          aria-label="Close settings"
        >
          <X size={16} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {/* Model */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">Model</label>
          <input
            type="text"
            value={settings.model}
            onChange={(e) => update({ model: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Temperature */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">
            Temperature ({settings.temperature.toFixed(1)})
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={settings.temperature}
            onChange={(e) => update({ temperature: parseFloat(e.target.value) })}
            className="accent-brand-500"
          />
        </div>

        {/* Use agent */}
        <div className="flex items-center gap-2">
          <input
            id="use-agent"
            type="checkbox"
            checked={settings.useAgent}
            onChange={(e) => update({ useAgent: e.target.checked })}
            className="accent-brand-500 w-4 h-4"
          />
          <label htmlFor="use-agent" className="text-xs text-gray-400 cursor-pointer">
            Use LangChain Agent
          </label>
        </div>

        {/* Stream */}
        <div className="flex items-center gap-2">
          <input
            id="stream"
            type="checkbox"
            checked={settings.stream}
            onChange={(e) => update({ stream: e.target.checked })}
            className="accent-brand-500 w-4 h-4"
          />
          <label htmlFor="stream" className="text-xs text-gray-400 cursor-pointer">
            Stream responses
          </label>
        </div>
      </div>
    </div>
  );
}
