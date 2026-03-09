<script lang="ts">
	import type { Community, GraphNode } from '$lib/types';
	import { communityColor } from '$lib/colors';

	let { communities, nodes }: { communities: Community[]; nodes: GraphNode[] } = $props();

	function topByPagerank(communityId: number, limit = 3): GraphNode[] {
		return nodes
			.filter((n) => n.community === communityId)
			.sort((a, b) => b.pagerank - a.pagerank)
			.slice(0, limit);
	}

	function bridgeNodes(): GraphNode[] {
		return nodes
			.filter((n) => n.betweenness_centrality > 0.05)
			.sort((a, b) => b.betweenness_centrality - a.betweenness_centrality)
			.slice(0, 5);
	}

	let bridges = $derived(bridgeNodes());
</script>

<div class="panel">
	<div class="panel-header">
		<span class="title">Communities</span>
		<span class="meta">{communities.length} detected</span>
	</div>

	<div class="panel-body">
		{#each communities as community (community.id)}
			<div class="community-card">
				<div class="community-header">
					<span class="dot" style="background: {communityColor(community.id)}"></span>
					<span class="community-label">Community {community.id}</span>
					<span class="community-size">{community.size} members</span>
				</div>
				<div class="members">
					{#each community.members as member}
						<span class="member-tag">{member}</span>
					{/each}
				</div>
				<div class="top-ranked">
					{#each topByPagerank(community.id) as node, i}
						<div class="rank-row">
							<span class="rank">#{i + 1}</span>
							<span class="rank-name">{node.id}</span>
							<span class="rank-value">PR {node.pagerank.toFixed(4)}</span>
						</div>
					{/each}
				</div>
			</div>
		{/each}

		{#if bridges.length > 0}
			<div class="bridge-section">
				<div class="bridge-header">Cross-Community Bridges</div>
				{#each bridges as node}
					<div class="bridge-row">
						<span class="dot" style="background: {communityColor(node.community)}"></span>
						<span class="bridge-name">{node.id}</span>
						<span class="bridge-value">betw. {node.betweenness_centrality.toFixed(3)}</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.panel {
		background: var(--bg-card);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.panel-header {
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

	.panel-body {
		padding: 0.75rem 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		max-height: 400px;
		overflow-y: auto;
	}

	.community-card {
		background: var(--bg-secondary);
		border-radius: var(--radius-sm);
		padding: 0.6rem 0.75rem;
	}

	.community-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.4rem;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.community-label {
		font-weight: 600;
		font-size: 0.82rem;
		color: var(--text-primary);
	}

	.community-size {
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
		margin-left: auto;
	}

	.members {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
		margin-bottom: 0.4rem;
	}

	.member-tag {
		font-size: 0.72rem;
		padding: 0.15rem 0.5rem;
		background: var(--bg-hover);
		border-radius: 9999px;
		color: var(--text-secondary);
	}

	.top-ranked {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.rank-row {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.72rem;
		font-family: var(--font-mono);
		color: var(--text-secondary);
	}

	.rank {
		color: var(--text-muted);
		width: 1.5rem;
	}

	.rank-name {
		flex: 1;
		color: var(--text-primary);
	}

	.rank-value {
		color: var(--text-muted);
	}

	.bridge-section {
		border-top: 1px solid var(--border);
		padding-top: 0.6rem;
	}

	.bridge-header {
		font-weight: 600;
		font-size: 0.82rem;
		color: var(--text-primary);
		margin-bottom: 0.4rem;
	}

	.bridge-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.78rem;
		padding: 0.2rem 0;
	}

	.bridge-name {
		flex: 1;
		color: var(--text-primary);
	}

	.bridge-value {
		color: var(--text-muted);
		font-family: var(--font-mono);
		font-size: 0.72rem;
	}
</style>
