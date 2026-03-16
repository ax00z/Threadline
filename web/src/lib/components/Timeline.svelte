<script lang="ts">
	import { onMount } from 'svelte';
	import type { Message } from '$lib/types';
	import { filterState, setTimeRange, clearTimeRange } from '$lib/selection.svelte';
	import {
		Chart,
		BarController,
		CategoryScale,
		LinearScale,
		BarElement,
		Tooltip
	} from 'chart.js';

	Chart.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip);

	let { messages }: { messages: Message[] } = $props();

	let canvas: HTMLCanvasElement;
	let chart: Chart | undefined;
	let allLabels: string[] = [];
	let baseColor = '#2d7ff940';
	let dimColor = '#2d7ff912';
	let accentColor = '#2d7ff9';
	let collapsed = $state(false);

	let dragStartIdx: number | null = null;
	let dragEndIdx: number | null = null;
	let isDragging = false;

	function buildDailyCounts() {
		const counts = new Map<string, number>();
		for (const m of messages) {
			const day = m.timestamp.slice(0, 10);
			counts.set(day, (counts.get(day) || 0) + 1);
		}
		const sorted = [...counts.keys()].sort();
		if (sorted.length < 2)
			return { labels: sorted, values: sorted.map((d) => counts.get(d) || 0) };
		const start = new Date(sorted[0]);
		const end = new Date(sorted[sorted.length - 1]);
		const labels: string[] = [];
		const values: number[] = [];
		for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
			const key = d.toISOString().slice(0, 10);
			labels.push(key);
			values.push(counts.get(key) || 0);
		}
		return { labels, values };
	}

	function getBarIndex(e: MouseEvent): number | null {
		if (!chart) return null;
		const rect = canvas.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const xScale = chart.scales.x;
		if (!xScale) return null;
		let closest = -1;
		let closestDist = Infinity;
		for (let i = 0; i < allLabels.length; i++) {
			const px = xScale.getPixelForValue(i);
			const dist = Math.abs(px - x);
			if (dist < closestDist) {
				closestDist = dist;
				closest = i;
			}
		}
		return closest >= 0 ? closest : null;
	}

	function handleMouseDown(e: MouseEvent) {
		const idx = getBarIndex(e);
		if (idx === null) return;
		isDragging = true;
		dragStartIdx = idx;
		dragEndIdx = idx;
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isDragging) return;
		const idx = getBarIndex(e);
		if (idx !== null) dragEndIdx = idx;
		updateBrushVisuals();
	}

	function handleMouseUp() {
		if (!isDragging) return;
		isDragging = false;
		if (dragStartIdx !== null && dragEndIdx !== null) {
			const lo = Math.min(dragStartIdx, dragEndIdx);
			const hi = Math.max(dragStartIdx, dragEndIdx);
			const startDate = allLabels[lo];
			const endDate = allLabels[hi];
			setTimeRange(startDate + 'T00:00:00', endDate + 'T23:59:59');
		}
		updateBrushVisuals();
	}

	function updateBrushVisuals() {
		if (!chart || !chart.data.datasets[0]) return;
		const ds = chart.data.datasets[0];
		if (dragStartIdx !== null && dragEndIdx !== null) {
			const lo = Math.min(dragStartIdx, dragEndIdx);
			const hi = Math.max(dragStartIdx, dragEndIdx);
			ds.backgroundColor = allLabels.map((_, i) =>
				i >= lo && i <= hi ? baseColor : dimColor
			) as any;
			ds.borderColor = allLabels.map((_, i) =>
				i >= lo && i <= hi ? accentColor : accentColor + '30'
			) as any;
		}
		chart.update('none');
	}

	function handleClearRange() {
		clearTimeRange();
		dragStartIdx = null;
		dragEndIdx = null;
		if (chart && chart.data.datasets[0]) {
			chart.data.datasets[0].backgroundColor = baseColor;
			chart.data.datasets[0].borderColor = accentColor;
			chart.update('none');
		}
	}

	$effect(() => {
		if (!filterState.timeRange && chart && chart.data.datasets[0]) {
			dragStartIdx = null;
			dragEndIdx = null;
			chart.data.datasets[0].backgroundColor = baseColor;
			chart.data.datasets[0].borderColor = accentColor;
			chart.update('none');
		}
	});

	onMount(() => {
		const dc = buildDailyCounts();
		allLabels = dc.labels;
		if (dc.labels.length === 0) return;

		requestAnimationFrame(() => {
			if (collapsed) return;
			chart = new Chart(canvas, {
				type: 'bar',
				data: {
					labels: dc.labels,
					datasets: [
						{
							data: dc.values,
							backgroundColor: baseColor,
							borderColor: accentColor,
							borderWidth: 1,
							borderRadius: 2
						}
					]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					animation: false,
					plugins: {
						legend: { display: false },
						tooltip: {
							callbacks: {
								title: (items: any[]) => {
									const d = new Date(items[0].label);
									return d.toLocaleDateString('en-US', {
										weekday: 'short',
										month: 'short',
										day: 'numeric',
										year: 'numeric'
									});
								},
								label: (ctx: any) => `${ctx.raw.toLocaleString()} messages`
							}
						}
					},
					scales: {
						x: {
							grid: { color: '#1b2535' },
							ticks: {
								color: '#768390',
								maxRotation: 0,
								maxTicksLimit: 12,
								callback: function (_: any, index: number) {
									const label = dc.labels[index];
									if (!label) return '';
									const d = new Date(label);
									return d.toLocaleDateString('en-US', {
										month: 'short',
										day: 'numeric'
									});
								}
							}
						},
						y: {
							beginAtZero: true,
							grid: { color: '#1b2535' },
							ticks: { color: '#768390' }
						}
					}
				}
			});

			canvas.addEventListener('mousedown', handleMouseDown);
			canvas.addEventListener('mousemove', handleMouseMove);
			canvas.addEventListener('mouseup', handleMouseUp);
			canvas.addEventListener('mouseleave', () => {
				if (isDragging) handleMouseUp();
			});
		});

		return () => {
			canvas?.removeEventListener('mousedown', handleMouseDown);
			canvas?.removeEventListener('mousemove', handleMouseMove);
			canvas?.removeEventListener('mouseup', handleMouseUp);
			chart?.destroy();
		};
	});
</script>

<div class="timeline">
	<button class="section-toggle" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="toggle-title">Activity Over Time</span>
		{#if filterState.timeRange}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<span class="clear-range" role="button" tabindex="-1" onclick={(e) => { e.stopPropagation(); handleClearRange(); }}>Clear range</span>
		{/if}
		<span class="hint">drag to select a time range</span>
	</button>
	{#if !collapsed}
		<div class="chart-area">
			<canvas bind:this={canvas}></canvas>
		</div>
	{/if}
</div>

<style>
	.timeline {
		background: var(--bg-card);
		border-radius: var(--radius);
	}

	.section-toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		cursor: pointer;
		color: var(--text-primary);
	}

	.section-toggle:hover { background: var(--bg-hover); }

	.toggle-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
	}

	.toggle-title {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--text-secondary);
		font-weight: 600;
	}

	.hint {
		font-size: 0.68rem;
		color: var(--text-muted);
		margin-left: auto;
	}

	.clear-range {
		background: none;
		border: 1px solid var(--accent);
		border-radius: var(--radius-sm);
		color: var(--accent);
		font-size: 0.68rem;
		padding: 0.15rem 0.4rem;
		cursor: pointer;
	}

	.clear-range:hover {
		background: var(--accent);
		color: #fff;
	}

	.chart-area {
		height: 200px;
		position: relative;
		cursor: crosshair;
		padding: 0.5rem 1rem 1rem;
	}
</style>
