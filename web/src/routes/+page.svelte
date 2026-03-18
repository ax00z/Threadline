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
	import SentimentPanel from '$lib/components/SentimentPanel.svelte';
	import HeatmapPanel from '$lib/components/HeatmapPanel.svelte';
	import ResponseTimePanel from '$lib/components/ResponseTimePanel.svelte';
	import QueryConsole from '$lib/components/QueryConsole.svelte';
	import IntelPanel from '$lib/components/IntelPanel.svelte';

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

				<section class="section-network">
					<div class="panel-graph">
						<NetworkGraph graph={data.graph} />
					</div>
					<div class="panel-groups">
						<CommunityPanel communities={data.graph.communities} nodes={data.graph.nodes} />
					</div>
				</section>

				<section class="section-timeline">
					<Timeline messages={data.messages} />
				</section>

				<section class="section-main">
					<div class="panel-people">
						<SenderStats senders={data.stats.senders} />
					</div>
					<div class="panel-messages">
						<MessageTable messages={data.messages} {senderColors} />
					</div>
				</section>

				<section class="section-duo">
					<div class="panel-entities">
						<EntityPanel ner={data.ner} />
					</div>
					<div class="panel-anomalies">
						<AnomalyPanel anomalies={data.anomalies} />
					</div>
				</section>

				<section class="section-relationships">
					<RelationshipTimeline pairwise={data.pairwise} />
				</section>

				<section class="section-intel">
					<IntelPanel intel={data.intel} />
				</section>

				<section class="section-insights">
					<div class="panel-sentiment">
						<SentimentPanel sentiment={data.sentiment} />
					</div>
					<div class="panel-heatmap">
						<HeatmapPanel heatmap={data.heatmap} />
					</div>
					<div class="panel-response">
						<ResponseTimePanel responseTimes={data.response_times} />
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
		gap: 0.75rem;
		padding: 0 1rem;
		height: 36px;
		border-bottom: 1px solid var(--border);
		background: var(--bg-secondary);
		flex-shrink: 0;
	}

	.logo {
		font-weight: 700;
		font-size: 0.78rem;
		letter-spacing: 0.18em;
		color: var(--text-label);
		font-family: var(--font-mono);
	}

	.file-label {
		color: var(--text-muted);
		font-size: 0.75rem;
		font-family: var(--font-mono);
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		padding-left: 0.75rem;
		border-left: 1px solid var(--border);
	}

	.btn-new {
		background: transparent;
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-muted);
		padding: 0.2rem 0.6rem;
		font-size: 0.7rem;
		font-family: var(--font-mono);
		cursor: pointer;
		white-space: nowrap;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.1s;
	}

	.btn-new:hover {
		border-color: var(--accent);
		color: var(--accent);
	}

	main {
		flex: 1;
		overflow-y: auto;
		padding: 0.75rem;
		min-height: 0;
	}

	.center-wrap {
		max-width: 560px;
		margin: 6rem auto;
	}

	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		max-width: 1800px;
		margin: 0 auto;
		padding-bottom: 2rem;
	}

	.selection-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.3rem 0.75rem;
		background: var(--bg-card);
		border-left: 2px solid var(--accent);
		font-size: 0.72rem;
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
		color: var(--text-muted);
		font-size: 0.7rem;
		font-family: var(--font-mono);
		cursor: pointer;
		padding: 0.1rem 0.3rem;
		flex-shrink: 0;
		text-transform: uppercase;
	}

	.selection-clear:hover {
		color: var(--text-primary);
	}

	.section-stats {
		flex-shrink: 0;
	}

	.section-main {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.panel-people {
		flex: 0 0 260px;
		min-width: 0;
	}

	.panel-messages {
		flex: 1 1 400px;
		min-width: 0;
	}

	.section-network {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.panel-graph {
		flex: 1 1 500px;
		min-width: 0;
	}

	.panel-groups {
		flex: 0 0 260px;
		min-width: 0;
	}

	.section-duo {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.panel-entities,
	.panel-anomalies {
		flex: 1 1 300px;
		min-width: 0;
	}

	.section-insights {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}

	.panel-sentiment,
	.panel-heatmap,
	.panel-response {
		flex: 1 1 250px;
		min-width: 0;
	}

	.section-timeline,
	.section-relationships,
	.section-intel,
	.section-advanced {
		flex-shrink: 0;
	}

	.section-stats :global(.toolbar) {
		margin-top: 0.4rem;
	}

	@media (max-width: 900px) {
		main {
			padding: 0.5rem;
		}

		.panel-people,
		.panel-graph,
		.panel-groups,
		.panel-entities,
		.panel-anomalies,
		.panel-sentiment,
		.panel-heatmap,
		.panel-response {
			flex-basis: 100%;
		}
	}

	@media (max-width: 600px) {
		header {
			padding: 0 0.5rem;
		}

		main {
			padding: 0.4rem;
		}

		.dashboard {
			gap: 0.5rem;
		}
	}

	.error-card {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-left: 2px solid var(--danger);
		padding: 1.5rem;
		text-align: center;
	}

	.error-title {
		font-weight: 600;
		font-size: 0.85rem;
		color: var(--danger);
		margin-bottom: 0.4rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.error-detail {
		color: var(--text-secondary);
		font-size: 0.8rem;
		font-family: var(--font-mono);
		margin-bottom: 1.2rem;
	}

	.error-card button {
		background: transparent;
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		padding: 0.35rem 1rem;
		cursor: pointer;
		font-size: 0.75rem;
		font-family: var(--font-mono);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.1s;
	}

	.error-card button:hover {
		border-color: var(--accent);
		color: var(--accent);
	}
</style>
