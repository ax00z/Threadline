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

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		if (disabled) return;
		const file = e.dataTransfer?.files[0];
		if (file && file.name.endsWith('.txt')) {
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
	<input bind:this={fileInput} type="file" accept=".txt" onchange={handleFileInput} hidden />

	{#if compact}
		<span class="compact-label">Upload new file</span>
	{:else}
		<div class="drop-icon">&#8613;</div>
		<p class="title">Drop WhatsApp export here</p>
		<p class="subtitle">or click to browse (.txt files)</p>
	{/if}
</div>

<style>
	.dropzone {
		border: 2px dashed var(--border);
		border-radius: var(--radius);
		padding: 4rem 2rem;
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
		font-size: 3rem;
		margin-bottom: 1rem;
		color: var(--text-muted);
	}

	.title {
		font-size: 1.2rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 0.4rem;
	}

	.subtitle {
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.compact-label {
		color: var(--text-secondary);
		font-size: 0.85rem;
	}
</style>
