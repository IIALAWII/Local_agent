"use client";

type SettingsPanelProps = {
	systemPrompt: string;
	onSystemPromptChange: (value: string) => void;
};

export default function SettingsPanel({
	systemPrompt,
	onSystemPromptChange,
}: SettingsPanelProps) {
	return (
		<section className="panel">
			<h2>Settings</h2>
			<label className="field">
				<span>System prompt</span>
				<textarea
					value={systemPrompt}
					onChange={(event) => onSystemPromptChange(event.target.value)}
					rows={5}
					placeholder="Optional assistant behavior instructions"
				/>
			</label>
			<p className="muted">Model is configured on backend as gpt-oss:20b via Ollama.</p>
		</section>
	);
}
