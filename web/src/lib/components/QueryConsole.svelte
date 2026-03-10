<script lang="ts">
	import { runQuery, type QueryResult } from '$lib/api';

	let sql = $state("SELECT sender, COUNT(*) as msg_count\nFROM messages\nGROUP BY sender\nORDER BY msg_count DESC");
	let result = $state<QueryResult | null>(null);
	let error = $state('');
	let loading = $state(false);
	let expanded = $state(false);

	const EXAMPLES = [
		{
			label: 'Messages per person',
			sql: 'SELECT sender, COUNT(*) as msg_count\nFROM messages\nGROUP BY sender\nORDER BY msg_count DESC'
		},
		{
			label: 'Search for a word',
			sql: "SELECT timestamp, sender, body\nFROM messages\nWHERE body ILIKE '%meet%'\nORDER BY timestamp"
		},
		{
			label: 'Busiest hours',
			sql: "SELECT SUBSTR(timestamp, 12, 2) as hour, COUNT(*) as msgs\nFROM messages\nGROUP BY hour\nORDER BY hour"
		},
		{
			label: 'Top 2 chatters',
			sql: "SELECT timestamp, sender, body\nFROM messages\nWHERE sender IN (\n  SELECT sender FROM messages\n  GROUP BY sender\n  ORDER BY COUNT(*) DESC LIMIT 2\n)\nORDER BY timestamp\nLIMIT 50"
		},
	];

	async function execute() {
		if (!sql.trim()) return;
		loading = true;
		error = '';
		result = null;
		try {
			result = await runQuery(sql);
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Query failed';
		} finally {
			loading = false;
		}
	}

	function loadExample(example: typeof EXAMPLES[0]) {
		sql = example.sql;
		result = null;
		error = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
			e.preventDefault();
			execute();
		}
	}
</script>

<div class="console">
	<button class="toggle-header" onclick={() => (expanded = !expanded)}>
		<span class="toggle-left">
			<span class="toggle-icon">{expanded ? '▾' : '▸'}</span>
			<span class="toggle-title">Advanced: Custom Queries</span>
		</span>
		<span class="toggle-hint">
			{#if !expanded}
				Click to write your own SQL queries
			{:else}
				DuckDB SQL &middot; Ctrl+Enter to run
			{/if}
		</span>
	</button>

	{#if expanded}
		<div class="console-body">
			<div class="examples">
				<span class="examples-label">Try:</span>
				{#each EXAMPLES as ex}
					<button class="example-btn" onclick={() => loadExample(ex)}>{ex.label}</button>
				{/each}
			</div>

			<div class="editor-area">
				<textarea
					class="sql-input"
					bind:value={sql}
					onkeydown={handleKeydown}
					rows="4"
					spellcheck="false"
					placeholder="Write a SQL query here..."
				></textarea>
				<button class="run-btn" onclick={execute} disabled={loading}>
					{loading ? 'Running...' : 'Run'}
				</button>
			</div>

			{#if error}
				<div class="error-msg">{error}</div>
			{/if}

			{#if result}
				<div class="result-meta">{result.row_count} {result.row_count === 1 ? 'result' : 'results'}</div>
				<div class="result-table-wrap">
					<table class="result-table">
						<thead>
							<tr>
								{#each result.columns as col}
									<th>{col}</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each result.rows as row}
								<tr>
									{#each row as cell}
										<td>{cell ?? 'NULL'}</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.console {
		background: var(--bg-card);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.toggle-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		cursor: pointer;
		color: var(--text-primary);
	}

	.toggle-header:hover {
		background: var(--bg-hover);
	}

	.toggle-left {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.toggle-icon {
		font-size: 0.75rem;
		color: var(--text-muted);
		width: 1rem;
	}

	.toggle-title {
		font-weight: 600;
		font-size: 0.88rem;
	}

	.toggle-hint {
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.console-body {
		border-top: 1px solid var(--border);
	}

	.examples {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid var(--border);
		flex-wrap: wrap;
	}

	.examples-label {
		font-size: 0.72rem;
		color: var(--text-muted);
		margin-right: 0.25rem;
	}

	.example-btn {
		font-size: 0.72rem;
		padding: 0.2rem 0.55rem;
		border-radius: 9999px;
		border: 1px solid var(--border);
		background: var(--bg-secondary);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}

	.example-btn:hover {
		border-color: var(--accent);
		color: var(--text-primary);
	}

	.editor-area {
		display: flex;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		align-items: flex-start;
	}

	.sql-input {
		flex: 1;
		background: var(--bg-primary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-primary);
		font-family: var(--font-mono);
		font-size: 0.8rem;
		padding: 0.6rem;
		resize: vertical;
		line-height: 1.5;
	}

	.sql-input:focus {
		outline: none;
		border-color: var(--accent);
	}

	.sql-input::placeholder {
		color: var(--text-muted);
	}

	.run-btn {
		background: var(--accent);
		border: none;
		border-radius: var(--radius-sm);
		color: #fff;
		padding: 0.5rem 1rem;
		font-size: 0.8rem;
		cursor: pointer;
		white-space: nowrap;
		flex-shrink: 0;
		transition: filter 0.15s;
	}

	.run-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.run-btn:hover:not(:disabled) {
		filter: brightness(1.1);
	}

	.error-msg {
		padding: 0.5rem 1rem;
		color: #f87171;
		font-size: 0.8rem;
		font-family: var(--font-mono);
	}

	.result-meta {
		padding: 0.3rem 1rem;
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.result-table-wrap {
		max-height: 300px;
		overflow: auto;
		margin: 0 0.5rem 0.5rem;
	}

	.result-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.78rem;
		font-family: var(--font-mono);
	}

	.result-table th {
		position: sticky;
		top: 0;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		font-weight: 600;
		text-align: left;
		padding: 0.4rem 0.6rem;
		border-bottom: 1px solid var(--border);
	}

	.result-table td {
		padding: 0.35rem 0.6rem;
		color: var(--text-primary);
		border-bottom: 1px solid var(--border);
		max-width: 400px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.result-table tbody tr:hover {
		background: var(--bg-hover);
	}
</style>
