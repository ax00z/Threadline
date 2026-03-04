<script lang="ts">
	import { uploadFile } from '$lib/api';
	import { buildSenderColorMap } from '$lib/colors';
	import type { UploadResponse } from '$lib/types';

	import DropZone from '$lib/components/DropZone.svelte';
	import ParseProgress from '$lib/components/ParseProgress.svelte';
	import StatsBar from '$lib/components/StatsBar.svelte';
	import MessageTable from '$lib/components/MessageTable.svelte';
	import SenderStats from '$lib/components/SenderStats.svelte';
	import Timeline from '$lib/components/Timeline.svelte';
	import GraphPlaceholder from '$lib/components/GraphPlaceholder.svelte';

	type View = 'idle' | 'uploading' | 'parsed' | 'error';

	let view = $state<View>('idle');
	let data = $state<UploadResponse | null>(null);
	let error = $state('');
	let fileName = $state('');

	let senderColors = $derived(
		data ? buildSenderColorMap(Object.keys(data.stats.senders)) : new Map()
	);

	async function handleFile(file: File) {
		fileName = file.name;
		view = 'uploading';
		error = '';
		try {
			data = await uploadFile(file);
			view = 'parsed';
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Unknown error';
			view = 'error';
		}
	}

	function reset() {
		view = 'idle';
		data = null;
		error = '';
		fileName = '';
	}
</script>

<div class="app">
	<header>
		<span class="logo">THREADLINE</span>
		{#if view === 'parsed'}
			<span class="file-label">{fileName}</span>
			<button class="btn-new" onclick={reset}>↥ Upload new file</button>
		{/if}
	</header>

	<main>
		{#if view === 'idle'}
			<div class="center-wrap">
				<DropZone onfileselected={handleFile} />
			</div>
		{:else if view === 'uploading'}
			<div class="center-wrap">
				<ParseProgress {fileName} />
			</div>
		{:else if view === 'error'}
			<div class="center-wrap">
				<div class="error-card">
					<p class="error-title">Failed to parse file</p>
					<p class="error-detail">{error}</p>
					<button onclick={reset}>Try again</button>
				</div>
			</div>
		{:else if view === 'parsed' && data}
			<div class="dashboard">
				<div class="row-stats">
					<StatsBar stats={data.stats} />
				</div>

				<div class="row-main">
					<div class="col-sidebar">
						<SenderStats senders={data.stats.senders} />
					</div>
					<div class="col-content">
						<MessageTable messages={data.messages} {senderColors} />
					</div>
				</div>

				<div class="row-timeline">
					<Timeline messages={data.messages} />
				</div>

				<div class="row-graph">
					<GraphPlaceholder />
				</div>
			</div>
		{/if}
	</main>
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
	}

	header {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 1.5rem;
		border-bottom: 1px solid var(--border);
		background: var(--bg-secondary);
		flex-shrink: 0;
	}

	.logo {
		font-weight: 700;
		font-size: 0.95rem;
		letter-spacing: 0.1em;
		color: var(--accent);
	}

	.file-label {
		color: var(--text-secondary);
		font-size: 0.85rem;
		font-family: var(--font-mono);
		flex: 1;
	}

	.btn-new {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		padding: 0.4rem 0.9rem;
		font-size: 0.82rem;
		cursor: pointer;
	}

	.btn-new:hover {
		border-color: var(--accent);
		color: var(--text-primary);
	}

	main {
		flex: 1;
		overflow-y: auto;
		padding: 1rem 1.5rem;
		min-height: 0;
	}

	.center-wrap {
		max-width: 640px;
		margin: 4rem auto;
	}

	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		height: 100%;
	}

	.row-stats {
		flex-shrink: 0;
	}

	.row-main {
		display: grid;
		grid-template-columns: 320px 1fr;
		gap: 1rem;
		min-height: 400px;
	}

	.col-sidebar {
		min-height: 0;
	}

	.col-content {
		min-height: 0;
	}

	.row-timeline {
		flex-shrink: 0;
	}

	.row-graph {
		flex-shrink: 0;
	}

	.error-card {
		background: var(--bg-card);
		border: 1px solid #f87171;
		border-radius: var(--radius);
		padding: 2rem;
		text-align: center;
	}

	.error-title {
		font-weight: 600;
		color: #f87171;
		margin-bottom: 0.5rem;
	}

	.error-detail {
		color: var(--text-secondary);
		font-size: 0.85rem;
		margin-bottom: 1.5rem;
	}

	.error-card button {
		background: var(--accent);
		border: none;
		border-radius: var(--radius-sm);
		color: #fff;
		padding: 0.5rem 1.2rem;
		cursor: pointer;
		font-size: 0.85rem;
	}
</style>
