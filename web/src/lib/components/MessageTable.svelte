<script lang="ts">
	import type { Message } from '$lib/types';

	let {
		messages,
		senderColors
	}: {
		messages: Message[];
		senderColors: Map<string, string>;
	} = $props();

	let search = $state('');

	let filtered = $derived(
		search
			? messages.filter(
					(m) =>
						m.body.toLowerCase().includes(search.toLowerCase()) ||
						m.sender.toLowerCase().includes(search.toLowerCase())
				)
			: messages
	);

	function fmtTime(iso: string): string {
		const d = new Date(iso);
		return (
			d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
			' ' +
			d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
		);
	}
</script>

<div class="table-wrap">
	<div class="search-bar">
		<input type="text" bind:value={search} placeholder="Search messages or senders…" />
		<span class="count">{filtered.length.toLocaleString()} messages</span>
	</div>

	<div class="scroll-area">
		{#each filtered as msg (msg.line_number)}
			<div class="row" style="border-left-color: {senderColors.get(msg.sender) || '#555'}">
				<span class="ts">{fmtTime(msg.timestamp)}</span>
				<span class="sender" style="color: {senderColors.get(msg.sender) || '#aaa'}"
					>{msg.sender}</span
				>
				<span class="body">{msg.body}</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.table-wrap {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--bg-card);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.search-bar {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.search-bar input {
		flex: 1;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.5rem 0.75rem;
		color: var(--text-primary);
		font-size: 0.85rem;
		outline: none;
	}

	.search-bar input:focus {
		border-color: var(--accent);
	}

	.search-bar input::placeholder {
		color: var(--text-muted);
	}

	.count {
		font-size: 0.75rem;
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.scroll-area {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		min-height: 0;
	}

	.row {
		display: flex;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		border-left: 3px solid transparent;
		border-bottom: 1px solid var(--border);
		font-size: 0.83rem;
		align-items: baseline;
	}

	.row:hover {
		background: var(--bg-hover);
	}

	.ts {
		color: var(--text-muted);
		font-family: var(--font-mono);
		font-size: 0.75rem;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.sender {
		font-weight: 600;
		font-size: 0.8rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex-shrink: 0;
		width: 120px;
	}

	.body {
		color: var(--text-primary);
		white-space: pre-wrap;
		word-break: break-word;
		flex: 1;
		min-width: 0;
	}
</style>
