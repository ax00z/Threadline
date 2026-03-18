<script lang="ts">
	import type { IntelResult } from '$lib/types';
	import { selectPerson } from '$lib/selection.svelte';

	let { intel }: { intel: IntelResult } = $props();
	let collapsed = $state(false);
	let activeTab = $state<'keywords' | 'topics' | 'threats'>('keywords');

	const THREAT_COLORS: Record<string, string> = {
		none: 'var(--text-muted)',
		low: '#57ab5a',
		medium: '#c69026',
		high: '#e5534b',
	};

	const CAT_COLORS: Record<string, string> = {
		violence: '#e5534b',
		narcotics: '#b083f0',
		financial: '#c69026',
		coercion: '#e07ab5',
		trafficking: '#d49e6a',
		cyber: '#2d7ff9',
		logistics: '#56b6c2',
		opsec: '#768390',
	};

	function fmtTime(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
			' ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
	}
</script>

<div class="panel">
	<button class="panel-header" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="panel-title">Intelligence</span>
		{#if intel.threats.level !== 'none'}
			<span class="threat-badge" style="background: {THREAT_COLORS[intel.threats.level]}">
				{intel.threats.level} threat
			</span>
		{/if}
		<span class="badge">{intel.keywords.length} keywords</span>
	</button>

	{#if !collapsed}
		<div class="tabs">
			<button class:active={activeTab === 'keywords'} onclick={() => activeTab = 'keywords'}>Keywords</button>
			<button class:active={activeTab === 'topics'} onclick={() => activeTab = 'topics'}>Topics</button>
			<button class:active={activeTab === 'threats'} onclick={() => activeTab = 'threats'}>
				Threats
				{#if intel.threats.flagged_count > 0}
					<span class="tab-count">{intel.threats.flagged_count}</span>
				{/if}
			</button>
		</div>

		{#if activeTab === 'keywords'}
			<div class="keyword-list">
				{#each intel.keywords.slice(0, 20) as kw}
					<div class="keyword-row">
						<span class="kw-word">{kw.keyword}</span>
						<span class="kw-count">{kw.count}x</span>
						<div class="kw-senders">
							{#each kw.senders.slice(0, 3) as sender}
								<button class="kw-sender" onclick={() => selectPerson(sender)}>{sender}</button>
							{/each}
							{#if kw.senders.length > 3}
								<span class="kw-more">+{kw.senders.length - 3}</span>
							{/if}
						</div>
					</div>
				{/each}
				{#if intel.keywords.length === 0}
					<div class="empty">Not enough data for keyword extraction</div>
				{/if}
			</div>

		{:else if activeTab === 'topics'}
			{#if !intel.topics.available}
				<div class="empty">Install scikit-learn for topic clustering</div>
			{:else if intel.topics.topics.length === 0}
				<div class="empty">Not enough data for topic clustering</div>
			{:else}
				<div class="topic-list">
					{#each intel.topics.topics as topic}
						<div class="topic-card">
							<div class="topic-header">
								<span class="topic-label">Topic {topic.id + 1}</span>
								<span class="topic-size">{topic.size} msgs</span>
							</div>
							<div class="topic-terms">
								{#each topic.top_terms as term}
									<span class="term-chip">{term}</span>
								{/each}
							</div>
							<div class="topic-senders">
								{#each topic.top_senders as sender}
									<button class="topic-sender" onclick={() => selectPerson(sender)}>{sender}</button>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			{/if}

		{:else if activeTab === 'threats'}
			<div class="threat-overview">
				<div class="threat-level" style="color: {THREAT_COLORS[intel.threats.level]}">
					{intel.threats.level.toUpperCase()}
				</div>
				<div class="threat-stats">
					{intel.threats.flagged_count} flagged / {intel.threats.total_messages} total
				</div>
			</div>

			{#if Object.keys(intel.threats.categories).length > 0}
				<div class="cat-bar">
					{#each Object.entries(intel.threats.categories) as [cat, count]}
						<div class="cat-chip" style="border-color: {CAT_COLORS[cat] || 'var(--border)'}">
							<span class="cat-name">{cat}</span>
							<span class="cat-count">{count}</span>
						</div>
					{/each}
				</div>
			{/if}

			{#if intel.threats.per_sender.length > 0}
				<div class="section-label">By sender</div>
				<div class="threat-senders">
					{#each intel.threats.per_sender as ts}
						<button class="ts-row" onclick={() => selectPerson(ts.sender)}>
							<span class="ts-name">{ts.sender}</span>
							<span class="ts-flagged">{ts.flagged_messages} flagged</span>
							<span class="ts-density">{(ts.threat_density * 100).toFixed(1)}%</span>
						</button>
					{/each}
				</div>
			{/if}

			{#if intel.threats.flagged.length > 0}
				<div class="section-label">Flagged messages</div>
				<div class="flagged-list">
					{#each intel.threats.flagged.slice(0, 20) as f}
						<div class="flagged-row">
							<div class="flagged-meta">
								<span class="flagged-sender">{f.sender}</span>
								<span class="flagged-ts">{fmtTime(f.timestamp)}</span>
								{#each f.categories as cat}
									<span class="flagged-cat" style="color: {CAT_COLORS[cat] || 'var(--text-muted)'}">{cat}</span>
								{/each}
							</div>
							<div class="flagged-body">{f.body}</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="empty">No flagged messages detected</div>
			{/if}
		{/if}
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

	.panel-title {
		font-weight: 600;
		font-size: 0.85rem;
		color: var(--text-primary);
	}

	.badge {
		background: var(--bg-secondary);
		color: var(--text-secondary);
		font-size: 0.68rem;
		padding: 0.15rem 0.5rem;
		border-radius: 9999px;
		font-family: var(--font-mono);
		margin-left: auto;
	}

	.threat-badge {
		font-size: 0.62rem;
		padding: 0.12rem 0.5rem;
		border-radius: 9999px;
		color: #000;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-family: var(--font-mono);
	}

	.tabs {
		display: flex;
		border-bottom: 1px solid var(--border);
	}

	.tabs button {
		flex: 1;
		padding: 0.45rem 0.5rem;
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		color: var(--text-muted);
		font-size: 0.72rem;
		font-family: var(--font-mono);
		cursor: pointer;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.1s;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.3rem;
	}

	.tabs button:hover { color: var(--text-secondary); }
	.tabs button.active {
		color: var(--accent);
		border-bottom-color: var(--accent);
	}

	.tab-count {
		background: var(--accent);
		color: #fff;
		font-size: 0.6rem;
		padding: 0.05rem 0.35rem;
		border-radius: 9999px;
	}

	/* Keywords */
	.keyword-list {
		max-height: 320px;
		overflow-y: auto;
	}

	.keyword-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.35rem 1rem;
		border-bottom: 1px solid var(--border);
		font-size: 0.78rem;
	}

	.kw-word {
		font-weight: 500;
		color: var(--text-primary);
		min-width: 80px;
	}

	.kw-count {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--text-muted);
		min-width: 32px;
	}

	.kw-senders {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
		margin-left: auto;
	}

	.kw-sender {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		font-size: 0.65rem;
		padding: 0.1rem 0.35rem;
		cursor: pointer;
		font-family: var(--font-mono);
	}

	.kw-sender:hover { border-color: var(--accent); color: var(--accent); }

	.kw-more {
		font-size: 0.62rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	/* Topics */
	.topic-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.5rem;
		max-height: 360px;
		overflow-y: auto;
	}

	.topic-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.6rem;
	}

	.topic-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.35rem;
	}

	.topic-label {
		font-weight: 600;
		font-size: 0.75rem;
		color: var(--text-primary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.topic-size {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--text-muted);
	}

	.topic-terms {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		margin-bottom: 0.3rem;
	}

	.term-chip {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.08rem 0.4rem;
		font-size: 0.68rem;
		color: var(--accent);
		font-family: var(--font-mono);
	}

	.topic-senders {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}

	.topic-sender {
		background: none;
		border: none;
		color: var(--text-muted);
		font-size: 0.65rem;
		cursor: pointer;
		padding: 0;
		font-family: var(--font-mono);
	}

	.topic-sender:hover { color: var(--accent); }

	/* Threats */
	.threat-overview {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.threat-level {
		font-size: 1.1rem;
		font-weight: 700;
		font-family: var(--font-mono);
		letter-spacing: 0.1em;
	}

	.threat-stats {
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.cat-bar {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
		padding: 0.5rem 1rem;
	}

	.cat-chip {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.15rem 0.5rem;
		border: 1px solid;
		border-radius: var(--radius-sm);
		font-size: 0.68rem;
	}

	.cat-name {
		color: var(--text-secondary);
		font-family: var(--font-mono);
	}

	.cat-count {
		color: var(--text-muted);
		font-family: var(--font-mono);
		font-size: 0.62rem;
	}

	.section-label {
		padding: 0.5rem 1rem 0.25rem;
		font-size: 0.68rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 600;
		border-top: 1px solid var(--border);
	}

	.threat-senders {
		max-height: 180px;
		overflow-y: auto;
	}

	.ts-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.35rem 1rem;
		border: none;
		border-bottom: 1px solid var(--border);
		background: none;
		color: var(--text-primary);
		cursor: pointer;
		font-size: 0.78rem;
		text-align: left;
	}

	.ts-row:hover { background: var(--bg-hover); }

	.ts-name {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.ts-flagged {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--text-muted);
	}

	.ts-density {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: #c69026;
		width: 40px;
		text-align: right;
	}

	.flagged-list {
		max-height: 280px;
		overflow-y: auto;
	}

	.flagged-row {
		padding: 0.4rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.flagged-meta {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-bottom: 0.2rem;
	}

	.flagged-sender {
		font-weight: 500;
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.flagged-ts {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--text-muted);
	}

	.flagged-cat {
		font-size: 0.62rem;
		font-family: var(--font-mono);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.flagged-body {
		font-size: 0.75rem;
		color: var(--text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.empty {
		padding: 1.5rem;
		text-align: center;
		color: var(--text-muted);
		font-size: 0.82rem;
	}
</style>
