<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import Graph from 'graphology';
	import Sigma from 'sigma';
	import forceAtlas2 from 'graphology-layout-forceatlas2';
	import { circular } from 'graphology-layout';
	import type { GraphData, GraphNode } from '$lib/types';
	import { communityColor } from '$lib/colors';
	import { filterState, selectPerson, selectEdge, clearSelection } from '$lib/selection.svelte';

	let { graph }: { graph: GraphData } = $props();

	let container: HTMLDivElement;
	let renderer: Sigma | null = null;
	let g: Graph | null = null;
	let hovered = $state<GraphNode | null>(null);

	function isNeighbor(nodeId: string, target: string): boolean {
		if (!g) return false;
		return g.hasEdge(nodeId, target) || g.hasEdge(target, nodeId);
	}

	function activeNodes(): Set<string> | null {
		const sel = filterState.selection;
		if (sel.kind === 'none') return null;
		const set = new Set<string>();
		if (sel.kind === 'person') {
			set.add(sel.sender);
			if (g) g.forEachNeighbor(sel.sender, (n) => set.add(n));
		} else if (sel.kind === 'edge') {
			set.add(sel.source);
			set.add(sel.target);
		} else if (sel.kind === 'entity') {
			sel.senders.forEach((s) => set.add(s));
		}
		return set;
	}

	function activeEdges(): Set<string> | null {
		const sel = filterState.selection;
		if (sel.kind === 'none' || !g) return null;
		const set = new Set<string>();
		if (sel.kind === 'person') {
			g.forEachEdge(sel.sender, (e) => set.add(e));
		} else if (sel.kind === 'edge') {
			g.forEachEdge((e, _attrs, src, tgt) => {
				if (
					(src === sel.source && tgt === sel.target) ||
					(src === sel.target && tgt === sel.source)
				) {
					set.add(e);
				}
			});
		} else if (sel.kind === 'entity') {
			const ss = new Set(sel.senders);
			g.forEachEdge((e, _attrs, src, tgt) => {
				if (ss.has(src) && ss.has(tgt)) set.add(e);
			});
		}
		return set;
	}

	onMount(() => {
		if (!graph.nodes.length) return;

		g = new Graph({ type: 'undirected', multi: false });

		graph.nodes.forEach((node) => {
			g!.addNode(node.id, {
				label: node.id,
				size: 5 + node.degree_centrality * 20,
				color: communityColor(node.community),
				message_count: node.message_count,
				degree_centrality: node.degree_centrality,
				betweenness_centrality: node.betweenness_centrality,
				closeness_centrality: node.closeness_centrality,
				pagerank: node.pagerank,
				community: node.community,
			});
		});

		graph.edges.forEach((edge) => {
			if (
				g!.hasNode(edge.source) &&
				g!.hasNode(edge.target) &&
				!g!.hasEdge(edge.source, edge.target)
			) {
				g!.addEdge(edge.source, edge.target, {
					size: Math.max(1, Math.min(edge.weight, 6)),
					color: '#374151',
					weight: edge.weight,
				});
			}
		});

		circular.assign(g!);
		forceAtlas2.assign(g!, {
			iterations: 200,
			settings: {
				gravity: 1,
				scalingRatio: 8,
				strongGravityMode: true,
			},
		});

		renderer = new Sigma(g!, container, {
			renderEdgeLabels: false,
			enableEdgeEvents: true,
			labelFont: 'Inter, monospace',
			labelSize: 11,
			labelColor: { color: '#cbd5e1' },
			defaultEdgeColor: '#374151',
		});

		renderer.on('enterNode', ({ node }) => {
			const attrs = g!.getNodeAttributes(node);
			hovered = {
				id: node,
				message_count: attrs.message_count,
				degree_centrality: attrs.degree_centrality,
				betweenness_centrality: attrs.betweenness_centrality,
				closeness_centrality: attrs.closeness_centrality,
				pagerank: attrs.pagerank,
				community: attrs.community,
			};
		});

		renderer.on('leaveNode', () => {
			hovered = null;
		});

		renderer.on('clickNode', ({ node }) => {
			selectPerson(node);
		});

		renderer.on('clickEdge', ({ edge }) => {
			const [src, tgt] = g!.extremities(edge);
			selectEdge(src, tgt);
		});

		renderer.on('clickStage', () => {
			clearSelection();
		});
	});

	// push visual changes into sigma whenever selection changes
	$effect(() => {
		if (!renderer || !g) return;
		const nodes = activeNodes();
		const edges = activeEdges();

		const sel = filterState.selection;
		renderer.setSetting('nodeReducer', (node: string, data: Record<string, any>) => {
			if (!nodes) return data;
			const res = { ...data };
			if (nodes.has(node)) {
				if (
					(sel.kind === 'person' && node === sel.sender) ||
					(sel.kind === 'edge' &&
						(node === sel.source || node === sel.target))
				) {
					res.size = data.size * 1.3;
					res.zIndex = 2;
				}
			} else {
				res.color = '#2a2d38';
				res.label = '';
				res.size = data.size * 0.6;
				res.zIndex = 0;
			}
			return res;
		});

		renderer.setSetting('edgeReducer', (edge: string, data: Record<string, any>) => {
			if (!edges) return data;
			const res = { ...data };
			if (edges.has(edge)) {
				res.color = '#4f8ff7';
				res.size = Math.max(data.size, 2);
				res.zIndex = 1;
			} else {
				res.color = '#1a1d24';
				res.size = 0.5;
				res.zIndex = 0;
			}
			return res;
		});

		renderer.refresh();
	});

	onDestroy(() => {
		renderer?.kill();
	});
</script>

<div class="graph-card">
	<div class="graph-header">
		<span class="title">Who Talks to Who</span>
		<span class="meta">{graph.nodes.length} people &middot; {graph.edges.length} connections</span>
	</div>

	{#if graph.nodes.length === 0}
		<div class="empty">Not enough data to build a network graph.</div>
	{:else}
		<div class="canvas-wrap" bind:this={container}></div>
	{/if}

	{#if hovered}
		<div class="tooltip">
			<div class="tooltip-name">{hovered.id}</div>
			<div class="tooltip-community" style="color: {communityColor(hovered.community)}">Group {hovered.community}</div>
			<div class="metrics">
				<div class="metric-row"><span>Messages sent</span><span>{hovered.message_count}</span></div>
				<div class="metric-row"><span>Influence score</span><span>{(hovered.pagerank * 100).toFixed(1)}%</span></div>
				<div class="metric-row"><span>Connections</span><span>{(hovered.degree_centrality * 100).toFixed(0)}%</span></div>
				<div class="metric-row"><span>Bridge role</span><span>{(hovered.betweenness_centrality * 100).toFixed(1)}%</span></div>
				<div class="metric-row"><span>Reachability</span><span>{(hovered.closeness_centrality * 100).toFixed(0)}%</span></div>
			</div>
		</div>
	{/if}
</div>

<style>
	.graph-card {
		background: var(--bg-card);
		border-radius: var(--radius);
		overflow: hidden;
		position: relative;
	}

	.graph-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.title {
		font-weight: 600;
		font-size: 0.88rem;
		color: var(--text-primary);
	}

	.meta {
		font-size: 0.78rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.canvas-wrap {
		height: 450px;
		width: 100%;
		background: var(--bg-secondary);
		cursor: grab;
	}

	.canvas-wrap:active {
		cursor: grabbing;
	}

	.empty {
		height: 200px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-muted);
		font-size: 0.85rem;
	}

	.tooltip {
		position: absolute;
		bottom: 1rem;
		left: 1rem;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.6rem 0.8rem;
		pointer-events: none;
		z-index: 10;
		min-width: 180px;
	}

	.tooltip-name {
		font-weight: 600;
		font-size: 0.88rem;
		color: var(--text-primary);
		margin-bottom: 0.15rem;
	}

	.tooltip-community {
		font-size: 0.72rem;
		font-weight: 500;
		margin-bottom: 0.4rem;
	}

	.metrics {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.metric-row {
		display: flex;
		justify-content: space-between;
		font-size: 0.78rem;
		color: var(--text-secondary);
		font-family: var(--font-mono);
	}
</style>
