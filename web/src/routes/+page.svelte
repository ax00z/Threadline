<script lang="ts">
	import { uploadFile } from '$lib/api';
	import { buildSenderColorMap } from '$lib/colors';
	import type { UploadResponse } from '$lib/types';
	import { filterState, clearAll } from '$lib/selection.svelte';

	import DropZone from '$lib/components/DropZone.svelte';
	import ParseProgress from '$lib/components/ParseProgress.svelte';
	import StatsBar from '$lib/components/StatsBar.svelte';
	import MessageTable from '$lib/components/MessageTable.svelte';
	import SenderStats from '$lib/components/SenderStats.svelte';
	import Timeline from '$lib/components/Timeline.svelte';
	import NetworkGraph from '$lib/components/NetworkGraph.svelte';
	import CommunityPanel from '$lib/components/CommunityPanel.svelte';
	import EntityPanel from '$lib/components/EntityPanel.svelte';
	import AnomalyPanel from '$lib/components/AnomalyPanel.svelte';
	import ExportToolbar from '$lib/components/ExportToolbar.svelte';
	import RelationshipTimeline from '$lib/components/RelationshipTimeline.svelte';
	import QueryConsole from '$lib/components/QueryConsole.svelte';

	type View = 'idle' | 'uploading' | 'parsed' | 'error';

	let view = $state<View>('idle');
	let data = $state<UploadResponse | null>(null);
	let error = $state('');
	let fileName = $state('');

	let senderColors = $derived(
		data ? buildSenderColorMap(Object.keys(data.stats.senders)) : new Map()
	);

	let hasFilter = $derived(filterState.selection.kind !== 'none' || filterState.timeRange !== null);

	let filterSummary = $derived.by(() => {
		const sel = filterState.selection;
		const tr = filterState.timeRange;
		const parts: string[] = [];
		if (sel.kind === 'person') parts.push(sel.sender);
		else if (sel.kind === 'edge') parts.push(`${sel.source} ↔ ${sel.target}`);
		else if (sel.kind === 'entity') parts.push(`${sel.label}: ${sel.text}`);
		else if (sel.kind === 'anomaly') parts.push(`Anomaly (${sel.indices.length} msgs)`);
		if (tr) {
			const fmt = (iso: string) => new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
			parts.push(`${fmt(tr.start)} – ${fmt(tr.end)}`);
		}
		return parts.join('  ·  ');
	});

	async function handleFile(file: File) {
		fileName = file.name;
		view = 'uploading';
		error = '';
		clearAll();
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
		clearAll();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && hasFilter) {
			clearAll();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="app">
	<header>
		<span class="logo">THREADLINE</span>
		{#if view === 'parsed'}
			<span class="file-label">{fileName}</span>
			<button class="btn-new" onclick={reset}>Upload new file</button>
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
					<p class="error-title">Something went wrong</p>
					<p class="error-detail">{error}</p>
					<button onclick={reset}>Try again</button>
				</div>
			</div>
		{:else if view === 'parsed' && data}
			<div class="dashboard">
				<section class="section-stats">
					<StatsBar stats={data.stats} chain={data.chain} />
					<ExportToolbar
						messages={data.messages}
						stats={data.stats}
						graph={data.graph}
						ner={data.ner}
						chain={data.chain}
						anomalies={data.anomalies}
						pairwise={data.pairwise}
					/>
				</section>

				{#if hasFilter}
					<div class="selection-bar">
						<span class="selection-text">{filterSummary}</span>
						<button class="selection-clear" onclick={clearAll}>Clear ✕</button>
					</div>
				{/if}

				<section class="section-main">
					<div class="panel-people">
						<SenderStats senders={data.stats.senders} />
					</div>
					<div class="panel-messages">
						<MessageTable messages={data.messages} {senderColors} />
					</div>
				</section>

				<section class="section-timeline">
					<Timeline messages={data.messages} />
				</section>

				<section class="section-entities">
					<EntityPanel ner={data.ner} />
				</section>

				<section class="section-anomalies">
					<AnomalyPanel anomalies={data.anomalies} />
				</section>

				<section class="section-relationships">
					<RelationshipTimeline pairwise={data.pairwise} />
				</section>

				<section class="section-network">
					<div class="panel-graph">
						<NetworkGraph graph={data.graph} />
					</div>
					<div class="panel-groups">
						<CommunityPanel communities={data.graph.communities} nodes={data.graph.nodes} />
					</div>
				</section>

				<section class="section-advanced">
					<QueryConsole />
				</section>
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
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.btn-new {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		padding: 0.4rem 0.9rem;
		font-size: 0.82rem;
		cursor: pointer;
		white-space: nowrap;
		transition: all 0.15s;
	}

	.btn-new:hover {
		border-color: var(--accent);
		color: var(--text-primary);
	}

	main {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
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
		max-width: 1600px;
		margin: 0 auto;
		padding-bottom: 2rem;
	}

	.selection-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.4rem 1rem;
		background: var(--bg-card);
		border: 1px solid var(--accent);
		border-radius: var(--radius-sm);
		font-size: 0.78rem;
	}

	.selection-text {
		color: var(--text-primary);
		font-family: var(--font-mono);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.selection-clear {
		background: none;
		border: none;
		color: var(--accent);
		font-size: 0.75rem;
		cursor: pointer;
		padding: 0.15rem 0.4rem;
		flex-shrink: 0;
	}

	.selection-clear:hover {
		color: var(--text-primary);
	}

	.section-stats {
		flex-shrink: 0;
	}

	.section-main {
		display: grid;
		grid-template-columns: minmax(240px, 320px) 1fr;
		gap: 1rem;
		min-height: 380px;
	}

	.panel-people,
	.panel-messages {
		min-height: 0;
		min-width: 0;
	}

	.section-network {
		display: grid;
		grid-template-columns: 1fr minmax(240px, 320px);
		gap: 1rem;
	}

	.panel-graph,
	.panel-groups {
		min-height: 0;
		min-width: 0;
	}

	.section-timeline,
	.section-entities,
	.section-anomalies,
	.section-relationships,
	.section-advanced {
		flex-shrink: 0;
	}

	.section-stats :global(.toolbar) {
		margin-top: 0.5rem;
	}

	@media (max-width: 900px) {
		main {
			padding: 0.75rem;
		}

		.section-main {
			grid-template-columns: 1fr;
			min-height: auto;
		}

		.section-network {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 600px) {
		header {
			padding: 0.5rem 0.75rem;
			gap: 0.5rem;
		}

		main {
			padding: 0.5rem;
		}

		.dashboard {
			gap: 0.75rem;
		}
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
