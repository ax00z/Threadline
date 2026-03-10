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
		<span class="compact-label">Upload new file</span>
	{:else}
		<div class="drop-icon">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
				<polyline points="17 8 12 3 7 8" />
				<line x1="12" y1="3" x2="12" y2="15" />
			</svg>
		</div>
		<p class="title">Drop your chat file here, or click to browse</p>
		<p class="subtitle">Supports WhatsApp exports, Telegram JSON, and CSV files</p>
		<div class="format-badges">
			<span class="badge">.txt</span>
			<span class="badge">.json</span>
			<span class="badge">.csv</span>
		</div>
	{/if}
</div>

<style>
	.dropzone {
		border: 2px dashed var(--border);
		border-radius: var(--radius);
		padding: 3.5rem 2rem;
		text-align: center;
		cursor: pointer;
		transition: all 0.2s;
		background: var(--bg-card);
	}

	.dropzone:hover,
	.dropzone.dragover {
		border-color: var(--accent);
		background: var(--accent-muted);
	}

	.dropzone.disabled {
		opacity: 0.5;
		pointer-events: none;
	}

	.dropzone.compact {
		padding: 0.6rem 1.2rem;
		border-style: solid;
		border-width: 1px;
		display: inline-block;
	}

	.drop-icon {
		margin-bottom: 1rem;
		color: var(--text-muted);
		transition: color 0.2s;
	}

	.dropzone:hover .drop-icon,
	.dropzone.dragover .drop-icon {
		color: var(--accent);
	}

	.title {
		font-size: 1.15rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 0.4rem;
	}

	.subtitle {
		color: var(--text-secondary);
		font-size: 0.88rem;
		margin-bottom: 1rem;
	}

	.format-badges {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
	}

	.badge {
		font-size: 0.72rem;
		font-family: var(--font-mono);
		padding: 0.2rem 0.6rem;
		border-radius: 9999px;
		background: var(--bg-secondary);
		color: var(--text-muted);
		border: 1px solid var(--border);
	}

	.compact-label {
		color: var(--text-secondary);
		font-size: 0.85rem;
	}
</style>
