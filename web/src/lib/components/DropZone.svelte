<script lang="ts">
	let {
		compact = false,
		disabled = false,
		onfileselected
	}: {
		compact?: boolean;
		disabled?: boolean;
		onfileselected?: (file: File) => void;
	} = $props();

	let dragOver = $state(false);
	let fileInput = $state<HTMLInputElement | undefined>();

	const ACCEPTED = ['.txt', '.json', '.csv'];

	function accepted(name: string) {
		return ACCEPTED.some((ext) => name.toLowerCase().endsWith(ext));
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		if (disabled) return;
		const file = e.dataTransfer?.files[0];
		if (file && accepted(file.name)) {
			onfileselected?.(file);
		}
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		if (!disabled) dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function handleFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) onfileselected?.(file);
	}

	function browse() {
		fileInput?.click();
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="dropzone"
	class:compact
	class:dragover={dragOver}
	class:disabled
	role="button"
	tabindex="0"
	ondrop={handleDrop}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	onclick={browse}
	onkeydown={(e) => e.key === 'Enter' && browse()}
>
	<input bind:this={fileInput} type="file" accept=".txt,.json,.csv" onchange={handleFileInput} hidden />

	{#if compact}
		<span class="compact-label">UPLOAD</span>
	{:else}
		<div class="drop-inner">
			<div class="icon-ring">
				<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
					<polyline points="17 8 12 3 7 8" />
					<line x1="12" y1="3" x2="12" y2="15" />
				</svg>
			</div>
			<p class="title">DROP EVIDENCE FILE</p>
			<p class="subtitle">WhatsApp exports, Telegram JSON, CSV surveillance logs</p>
			<div class="divider"></div>
			<div class="format-badges">
				{#each ACCEPTED as ext}
					<span class="badge">{ext}</span>
				{/each}
			</div>
			<p class="hint">or click to browse</p>
		</div>
	{/if}
</div>

<style>
	.dropzone {
		border: 1.5px dashed var(--text-muted);
		border-radius: 8px;
		padding: 3.5rem 2rem 2.5rem;
		text-align: center;
		cursor: pointer;
		transition: all 0.2s ease;
		background: var(--bg-card);
		position: relative;
		overflow: hidden;
	}

	/* top glow line */
	.dropzone::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(90deg, transparent 10%, var(--accent) 50%, transparent 90%);
		opacity: 0;
		transition: opacity 0.25s ease;
	}

	/* ambient background glow */
	.dropzone::after {
		content: '';
		position: absolute;
		top: -40%;
		left: 50%;
		transform: translateX(-50%);
		width: 60%;
		height: 70%;
		background: radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%);
		opacity: 0;
		transition: opacity 0.3s ease;
		pointer-events: none;
	}

	.dropzone:hover::before,
	.dropzone.dragover::before {
		opacity: 1;
	}

	.dropzone:hover::after,
	.dropzone.dragover::after {
		opacity: 1;
	}

	.dropzone:hover {
		border-color: var(--accent-dim);
		background: var(--bg-hover);
	}

	.dropzone.dragover {
		border-color: var(--accent);
		background: var(--bg-hover);
		box-shadow: 0 0 30px -8px var(--accent-glow);
	}

	.dropzone.disabled {
		opacity: 0.35;
		pointer-events: none;
	}

	.dropzone.compact {
		padding: 0.4rem 0.8rem;
		border-style: solid;
		border-width: 1px;
		display: inline-block;
		border-radius: var(--radius-sm);
	}

	.drop-inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		position: relative;
		z-index: 1;
	}

	.icon-ring {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		border: 1.5px solid var(--border);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-muted);
		margin-bottom: 0.6rem;
		transition: all 0.25s ease;
		background: var(--bg-secondary);
	}

	.dropzone:hover .icon-ring,
	.dropzone.dragover .icon-ring {
		color: var(--accent);
		border-color: var(--accent-dim);
		background: var(--accent-muted);
		transform: translateY(-2px);
	}

	.title {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--text-secondary);
		letter-spacing: 0.18em;
		font-family: var(--font-mono);
		transition: color 0.2s;
	}

	.dropzone:hover .title,
	.dropzone.dragover .title {
		color: var(--text-primary);
	}

	.subtitle {
		color: var(--text-muted);
		font-size: 0.78rem;
		max-width: 300px;
		line-height: 1.5;
	}

	.divider {
		width: 48px;
		height: 1px;
		background: var(--text-muted);
		margin: 0.5rem 0;
		opacity: 0.5;
	}

	.format-badges {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
		margin-top: 0.2rem;
	}

	.badge {
		font-size: 0.65rem;
		font-family: var(--font-mono);
		padding: 0.2rem 0.6rem;
		background: var(--bg-secondary);
		color: var(--text-muted);
		border: 1px solid var(--border);
		border-radius: 3px;
		letter-spacing: 0.04em;
		transition: all 0.2s;
	}

	.dropzone:hover .badge,
	.dropzone.dragover .badge {
		border-color: var(--border-subtle);
		color: var(--text-secondary);
	}

	.hint {
		font-size: 0.68rem;
		color: var(--text-secondary);
		margin-top: 0.3rem;
		opacity: 0.5;
		transition: opacity 0.2s;
	}

	.dropzone:hover .hint {
		opacity: 1;
	}

	.compact-label {
		color: var(--text-muted);
		font-size: 0.7rem;
		font-family: var(--font-mono);
		letter-spacing: 0.1em;
	}
</style>
