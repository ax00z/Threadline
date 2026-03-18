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
			<div class="drop-icon">
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
					<polyline points="17 8 12 3 7 8" />
					<line x1="12" y1="3" x2="12" y2="15" />
				</svg>
			</div>
			<p class="title">DROP EVIDENCE FILE</p>
			<p class="subtitle">WhatsApp exports, Telegram JSON, CSV surveillance logs</p>
			<div class="format-badges">
				<span class="badge">.txt</span>
				<span class="badge">.json</span>
				<span class="badge">.csv</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.dropzone {
		border: 1px solid var(--border);
		padding: 3rem 2rem;
		text-align: center;
		cursor: pointer;
		transition: all 0.15s;
		background: var(--bg-card);
		position: relative;
	}

	.dropzone::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, var(--accent-glow), transparent);
		opacity: 0;
		transition: opacity 0.15s;
	}

	.dropzone:hover::before,
	.dropzone.dragover::before {
		opacity: 1;
	}

	.dropzone:hover,
	.dropzone.dragover {
		border-color: var(--border);
		background: var(--bg-hover);
	}

	.dropzone.disabled {
		opacity: 0.4;
		pointer-events: none;
	}

	.dropzone.compact {
		padding: 0.4rem 0.8rem;
		border-style: solid;
		display: inline-block;
	}

	.drop-inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.6rem;
	}

	.drop-icon {
		color: var(--text-muted);
		transition: color 0.15s;
		margin-bottom: 0.4rem;
	}

	.dropzone:hover .drop-icon,
	.dropzone.dragover .drop-icon {
		color: var(--accent);
	}

	.title {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--text-secondary);
		letter-spacing: 0.15em;
		font-family: var(--font-mono);
	}

	.subtitle {
		color: var(--text-muted);
		font-size: 0.78rem;
	}

	.format-badges {
		display: flex;
		justify-content: center;
		gap: 0.4rem;
		margin-top: 0.4rem;
	}

	.badge {
		font-size: 0.65rem;
		font-family: var(--font-mono);
		padding: 0.15rem 0.5rem;
		background: var(--bg-secondary);
		color: var(--text-muted);
		border: 1px solid var(--border);
		letter-spacing: 0.03em;
	}

	.compact-label {
		color: var(--text-muted);
		font-size: 0.7rem;
		font-family: var(--font-mono);
		letter-spacing: 0.1em;
	}
</style>
