<script lang="ts">
	let { fileName = '' }: { fileName?: string } = $props();
</script>

<div class="progress-wrap">
	<div class="bar-track">
		<div class="bar-fill"></div>
	</div>
	<p class="label">Parsing {fileName}…</p>
</div>

<style>
	.progress-wrap {
		text-align: center;
		padding: 4rem 2rem;
	}

	.bar-track {
		width: 100%;
		max-width: 400px;
		height: 4px;
		background: var(--bg-card);
		border-radius: 2px;
		margin: 0 auto 1rem;
		overflow: hidden;
	}

	.bar-fill {
		width: 30%;
		height: 100%;
		background: var(--accent);
		border-radius: 2px;
		animation: slide 1.2s ease-in-out infinite;
	}

	@keyframes slide {
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(400%);
		}
	}

	.label {
		color: var(--text-secondary);
		font-size: 0.9rem;
	}
</style>
