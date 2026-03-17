<script lang="ts">
	import type { Community, GraphNode } from '$lib/types';
	import { communityColor } from '$lib/colors';
	import { filterState, selectPerson } from '$lib/selection.svelte';

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

	function isSelected(name: string) {
		return filterState.selection.kind === 'person' && filterState.selection.sender === name;
	}

	let bridges = $derived(bridgeNodes());
	let collapsed = $state(false);
</script>

<div class="panel">
	<button class="panel-header" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="title">Groups Found</span>
		<span class="meta">{communities.length} detected</span>
	</button>

	{#if !collapsed}
	<div class="panel-body">
		{#each communities as community (community.id)}
			<div class="community-card">
				<div class="community-header">
					<span class="dot" style="background: {communityColor(community.id)}"></span>
					<span class="community-label">Group {community.id}</span>
					<span class="community-size">{community.size} {community.size === 1 ? 'person' : 'people'}</span>
				</div>
				<div class="members">
					{#each community.members as member}
						<button
							class="member-tag"
							class:member-active={isSelected(member)}
							onclick={() => selectPerson(member)}
						>
							{member}
						</button>
					{/each}
				</div>
				<div class="top-ranked">
					{#each topByPagerank(community.id) as node, i}
						<button class="rank-row" onclick={() => selectPerson(node.id)}>
							<span class="rank">#{i + 1}</span>
							<span class="rank-name">{node.id}</span>
							<span class="rank-value">{(node.pagerank * 100).toFixed(1)}%</span>
						</button>
					{/each}
				</div>
			</div>
		{/each}

		{#if bridges.length > 0}
			<div class="bridge-section">
				<div class="bridge-header">Key Connectors Between Groups</div>
				{#each bridges as node}
					<button class="bridge-row" onclick={() => selectPerson(node.id)}>
						<span class="dot" style="background: {communityColor(node.community)}"></span>
						<span class="bridge-name">{node.id}</span>
						<span class="bridge-value">{(node.betweenness_centrality * 100).toFixed(1)}% bridge score</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>
	{/if}
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
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem 1rem;
		border: none;
		background: none;
		cursor: pointer;
		color: var(--text-primary);
	}

	.panel-header:hover { background: var(--bg-hover); }

	.toggle-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
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
		margin-left: auto;
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
		border: 1px solid transparent;
		cursor: pointer;
		transition: all 0.12s;
	}

	.member-tag:hover {
		border-color: var(--accent);
		color: var(--text-primary);
	}

	.member-active {
		background: var(--accent);
		color: #fff;
		border-color: transparent;
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
		background: none;
		border: none;
		padding: 0.15rem 0;
		cursor: pointer;
		width: 100%;
		text-align: left;
	}

	.rank-row:hover .rank-name {
		color: var(--accent);
	}

	.rank {
		color: var(--text-muted);
		width: 1.5rem;
	}

	.rank-name {
		flex: 1;
		color: var(--text-primary);
		transition: color 0.12s;
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
		background: none;
		border: none;
		cursor: pointer;
		width: 100%;
		text-align: left;
	}

	.bridge-row:hover .bridge-name {
		color: var(--accent);
	}

	.bridge-name {
		flex: 1;
		color: var(--text-primary);
		transition: color 0.12s;
	}

	.bridge-value {
		color: var(--text-muted);
		font-family: var(--font-mono);
		font-size: 0.72rem;
	}
</style>
