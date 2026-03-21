const STORAGE_KEY = 'threadline-theme';

type Theme = 'dark' | 'light';

function getInitial(): Theme {
	if (typeof localStorage !== 'undefined') {
		const saved = localStorage.getItem(STORAGE_KEY);
		if (saved === 'light' || saved === 'dark') return saved;
	}
	return 'dark';
}

let current = $state<Theme>(getInitial());

export const theme = {
	get value() { return current; },
	toggle() {
		current = current === 'dark' ? 'light' : 'dark';
		document.documentElement.setAttribute('data-theme', current);
		localStorage.setItem(STORAGE_KEY, current);
	},
	init() {
		document.documentElement.setAttribute('data-theme', current);
	}
};
