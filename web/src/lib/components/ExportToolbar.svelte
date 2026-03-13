<script lang="ts">
	import type { Message, ParseStats, GraphData, NerResult, ChainResult, Anomaly, PairwiseStats } from '$lib/types';
	import { filterState } from '$lib/selection.svelte';
	import { filterMessages } from '$lib/filters';

	let {
		messages,
		stats,
		graph,
		ner,
		chain,
		anomalies,
		pairwise
	}: {
		messages: Message[];
		stats: ParseStats;
		graph: GraphData;
		ner: NerResult;
		chain: ChainResult;
		anomalies: Anomaly[];
		pairwise: PairwiseStats[];
	} = $props();

	function download(content: string, filename: string, mime: string) {
		const blob = new Blob([content], { type: mime });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		a.click();
		URL.revokeObjectURL(url);
	}

	function ts(): string {
		return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
	}

	function exportFiltered() {
		const filtered = filterMessages(messages, filterState.selection, filterState.timeRange);
		const lines = filtered.map((m) => JSON.stringify(m));
		download(lines.join('\n') + '\n', `threadline-filtered-${ts()}.jsonl`, 'application/x-ndjson');
	}

	function exportReport() {
		const topNodes = [...graph.nodes]
			.sort((a, b) => b.pagerank - a.pagerank)
			.slice(0, 5)
			.map((n) => ({ id: n.id, pagerank: n.pagerank, messages: n.message_count }));

		const topEntities = ner.unique_entities.slice(0, 10);
		const topPairs = pairwise.slice(0, 10);

		const sevCounts: Record<string, number> = {};
		const kindCounts: Record<string, number> = {};
		for (const a of anomalies) {
			sevCounts[a.severity] = (sevCounts[a.severity] || 0) + 1;
			kindCounts[a.kind] = (kindCounts[a.kind] || 0) + 1;
		}

		const report = {
			generated_at: new Date().toISOString(),
			stats,
			chain_verification: chain,
			graph_summary: {
				node_count: graph.nodes.length,
				edge_count: graph.edges.length,
				communities: graph.communities.length,
				top_nodes_by_pagerank: topNodes,
			},
			entity_summary: {
				total_entities: ner.total_found,
				by_type: ner.label_counts,
				top_entities: topEntities,
			},
			anomaly_summary: {
				total: anomalies.length,
				by_kind: kindCounts,
				by_severity: sevCounts,
				items: anomalies,
			},
			pairwise_summary: {
				total_pairs: pairwise.length,
				top_pairs: topPairs,
			},
		};

		download(JSON.stringify(report, null, 2), `threadline-report-${ts()}.json`, 'application/json');
	}

	let hasFilter = $derived(filterState.selection.kind !== 'none' || filterState.timeRange !== null);
</script>

<div class="toolbar">
	<button class="toolbar-btn" onclick={exportFiltered}>
		{hasFilter ? 'Export Filtered' : 'Export All'} (JSONL)
	</button>
	<button class="toolbar-btn" onclick={exportReport}>
		Export Report (JSON)
	</button>
</div>

<style>
	.toolbar {
		display: flex;
		gap: 0.5rem;
	}

	.toolbar-btn {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		font-size: 0.78rem;
		padding: 0.4rem 0.85rem;
		cursor: pointer;
		transition: all 0.12s;
		white-space: nowrap;
	}

	.toolbar-btn:hover {
		border-color: var(--accent);
		color: var(--text-primary);
	}
</style>
