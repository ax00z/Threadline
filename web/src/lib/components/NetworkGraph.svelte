<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import Graph from 'graphology';
	import Sigma from 'sigma';
	import forceAtlas2 from 'graphology-layout-forceatlas2';
	import { circular } from 'graphology-layout';
	import type { GraphData, GraphNode } from '$lib/types';
	import { communityColor, nodeColor } from '$lib/colors';
	import { filterState, selectPerson, selectEdge, clearSelection } from '$lib/selection.svelte';

	let { graph }: { graph: GraphData } = $props();

	let container: HTMLDivElement;
	let renderer: Sigma | null = null;
	let g: Graph | null = null;
	let hovered = $state<GraphNode | null>(null);
	let collapsed = $state(false);

	// drag state
	let draggedNode: string | null = null;
	let isDragging = false;

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

		// Compute relative node sizes based on pagerank
		const pageranks = graph.nodes.map((n) => n.pagerank);
		const maxPR = Math.max(...pageranks, 0.001);
		const minPR = Math.min(...pageranks);
		const prRange = maxPR - minPR || 1;
		const MIN_SIZE = 4;
		const MAX_SIZE = 16;

		graph.nodes.forEach((node, idx) => {
			const color = nodeColor(idx);
			const normalized = (node.pagerank - minPR) / prRange;
			const size = MIN_SIZE + normalized * (MAX_SIZE - MIN_SIZE);
			g!.addNode(node.id, {
				label: node.id,
				size,
				color: color,
				message_count: node.message_count,
				degree_centrality: node.degree_centrality,
				betweenness_centrality: node.betweenness_centrality,
				closeness_centrality: node.closeness_centrality,
				pagerank: node.pagerank,
				community: node.community,
			});
		});

		// Compute relative edge sizes based on weight
		const weights = graph.edges.map((e) => e.weight);
		const maxW = Math.max(...weights, 1);

		graph.edges.forEach((edge) => {
			if (
				g!.hasNode(edge.source) &&
				g!.hasNode(edge.target) &&
				!g!.hasEdge(edge.source, edge.target)
			) {
				const normalizedW = edge.weight / maxW;
				g!.addEdge(edge.source, edge.target, {
					size: 0.4 + normalizedW * 1.6,
					color: '#8b949e30',
					weight: edge.weight,
				});
			}
		});

		circular.assign(g!);
		forceAtlas2.assign(g!, {
			iterations: 300,
			settings: {
				gravity: 0.5,
				scalingRatio: 50,
				strongGravityMode: false,
				barnesHutOptimize: true,
			},
		});

		renderer = new Sigma(g!, container, {
			renderEdgeLabels: false,
			enableEdgeEvents: true,
			labelFont: '"Inter", sans-serif',
			labelSize: 11,
			labelWeight: '500',
			labelColor: { color: '#cdd9e5' },
			defaultEdgeColor: '#8b949e30',
			defaultNodeType: 'circle',
			stagePadding: 60,
			labelRenderedSizeThreshold: 0,
		});

		// --- Node drag support ---
		renderer.on('downNode', (e) => {
			isDragging = true;
			draggedNode = e.node;
			// disable camera movement while dragging
			renderer!.getCamera().disable();
		});

		renderer.getMouseCaptor().on('mousemovebody', (e: any) => {
			if (!isDragging || !draggedNode || !renderer || !g) return;
			// convert viewport coords to graph coords
			const pos = renderer.viewportToGraph(e);
			g.setNodeAttribute(draggedNode, 'x', pos.x);
			g.setNodeAttribute(draggedNode, 'y', pos.y);
		});

		renderer.getMouseCaptor().on('mouseup', () => {
			if (isDragging && draggedNode) {
				isDragging = false;
				draggedNode = null;
				renderer?.getCamera().enable();
			}
		});

		renderer.getMouseCaptor().on('mousedown', () => {
			// if clicking empty space (not a node), ensure we're not dragging
			if (!renderer?.getCustomBBox()) return;
		});

		renderer.on('enterNode', ({ node }) => {
			if (isDragging) return;
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
			container.style.cursor = 'grab';
		});

		renderer.on('leaveNode', () => {
			hovered = null;
			if (!isDragging) container.style.cursor = 'default';
		});

		renderer.on('clickNode', ({ node }) => {
			if (!isDragging) selectPerson(node);
		});

		renderer.on('clickEdge', ({ edge }) => {
			const [src, tgt] = g!.extremities(edge);
			selectEdge(src, tgt);
		});

		renderer.on('clickStage', () => {
			if (!isDragging) clearSelection();
		});
	});

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
				res.color = '#1b253580';
				res.label = '';
				res.size = data.size * 0.5;
				res.zIndex = 0;
			}
			return res;
		});

		renderer.setSetting('edgeReducer', (edge: string, data: Record<string, any>) => {
			if (!edges) return data;
			const res = { ...data };
			if (edges.has(edge)) {
				res.color = '#2d7ff9aa';
				res.size = Math.max(data.size, 1.2);
				res.zIndex = 1;
			} else {
				res.color = '#0a0e1400';
				res.size = 0.15;
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
	<button class="graph-header" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="title">Network Analysis</span>
		<span class="hint">drag nodes to rearrange</span>
		<span class="meta">{graph.nodes.length} nodes &middot; {graph.edges.length} edges</span>
	</button>

	{#if !collapsed}
		{#if graph.nodes.length === 0}
			<div class="empty">Not enough data to build a network graph.</div>
		{:else}
			<div class="canvas-wrap" bind:this={container}></div>
		{/if}
	{/if}

	{#if !collapsed && hovered}
		<div class="tooltip">
			<div class="tooltip-name">{hovered.id}</div>
			<div class="tooltip-community" style="color: {communityColor(hovered.community)}">
				<span class="community-dot" style="background: {communityColor(hovered.community)}"></span>
				Cluster {hovered.community}
			</div>
			<div class="metrics">
				<div class="metric-row"><span class="metric-label">Messages</span><span class="metric-val">{hovered.message_count}</span></div>
				<div class="metric-row"><span class="metric-label">Influence</span><span class="metric-val">{(hovered.pagerank * 100).toFixed(1)}%</span></div>
				<div class="metric-row"><span class="metric-label">Connectivity</span><span class="metric-val">{(hovered.degree_centrality * 100).toFixed(0)}%</span></div>
				<div class="metric-row"><span class="metric-label">Bridge Score</span><span class="metric-val">{(hovered.betweenness_centrality * 100).toFixed(1)}%</span></div>
				<div class="metric-row"><span class="metric-label">Reach</span><span class="metric-val">{(hovered.closeness_centrality * 100).toFixed(0)}%</span></div>
			</div>
		</div>
	{/if}
</div>

<style>
	.graph-card {
		background: #060a10;
		border-radius: var(--radius);
		overflow: hidden;
		position: relative;
		border: 1px solid var(--border);
	}

	.graph-header {
		display: flex;
		align-items: center;
		width: 100%;
		padding: 0.65rem 1rem;
		border: none;
		border-bottom: 1px solid #111b28;
		background: #080c14;
		gap: 0.5rem;
		cursor: pointer;
		color: var(--text-primary);
	}

	.graph-header:hover { background: #0c1018; }

	.toggle-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
	}

	.title {
		font-weight: 600;
		font-size: 0.82rem;
		color: var(--text-primary);
		letter-spacing: 0.02em;
	}

	.hint {
		font-size: 0.68rem;
		color: var(--text-muted);
		flex: 1;
	}

	.meta {
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.canvas-wrap {
		height: 500px;
		width: 100%;
		background: radial-gradient(ellipse at center, #0c1220 0%, #060a10 70%, #030508 100%);
		cursor: default;
		position: relative;
	}

	.canvas-wrap::before {
		content: '';
		position: absolute;
		inset: 0;
		background:
			linear-gradient(rgba(45, 127, 249, 0.03) 1px, transparent 1px),
			linear-gradient(90deg, rgba(45, 127, 249, 0.03) 1px, transparent 1px);
		background-size: 40px 40px;
		pointer-events: none;
		z-index: 1;
	}

	.empty {
		height: 200px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-muted);
		font-size: 0.82rem;
	}

	.tooltip {
		position: absolute;
		bottom: 1rem;
		left: 1rem;
		background: #0a0f18ee;
		border: 1px solid #1b2535;
		border-radius: var(--radius-sm);
		padding: 0.65rem 0.85rem;
		pointer-events: none;
		z-index: 10;
		min-width: 190px;
		backdrop-filter: blur(12px);
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
	}

	.tooltip-name {
		font-weight: 600;
		font-size: 0.88rem;
		color: #e6edf3;
		margin-bottom: 0.2rem;
	}

	.tooltip-community {
		font-size: 0.7rem;
		font-weight: 500;
		margin-bottom: 0.5rem;
		display: flex;
		align-items: center;
		gap: 0.35rem;
	}

	.community-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		display: inline-block;
	}

	.metrics {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.metric-row {
		display: flex;
		justify-content: space-between;
		font-size: 0.72rem;
		font-family: var(--font-mono);
	}

	.metric-label {
		color: var(--text-muted);
	}

	.metric-val {
		color: var(--text-secondary);
	}
</style>
