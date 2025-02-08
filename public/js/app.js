class ScratcherAnalytics {
    constructor() {
        this.data = null;
        this.initializeElements();
        this.loadData();
    }

    initializeElements() {
        this.loading = document.getElementById('loading');
        this.gamesGrid = document.getElementById('gamesGrid');
        this.searchInput = document.getElementById('searchInput');
        this.sortSelect = document.getElementById('sortSelect');
        this.lastUpdated = document.getElementById('lastUpdated');

        // Add event listeners
        this.searchInput.addEventListener('input', () => this.updateDisplay());
        this.sortSelect.addEventListener('change', () => this.updateDisplay());
    }

    async loadData() {
        try {
            const response = await fetch('./web_data/current_analysis.json');
            if (!response.ok) throw new Error('Failed to load game data');
            
            this.data = await response.json();
            console.log('Loaded data:', this.data);
            
            this.updateDisplay();
            this.loading.style.display = 'none';
            this.gamesGrid.style.display = 'flex';
            
            // Update timestamp
            const timestamp = new Date().toLocaleString();
            this.lastUpdated.textContent = `Last updated: ${timestamp}`;
        } catch (error) {
            console.error('Error loading data:', error);
            this.loading.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load game data: ${error.message}
                </div>
            `;
        }
    }

    renderGameCard(game) {
        const imageUrl = game.image_url.trim() || "https://via.placeholder.com/400?text=No+Image";
        
        return `
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
            <div class="card game-card h-100">
                <div class="img-container">
                    <img src="${imageUrl}" class="card-img-top" alt="${game.name}">
                </div>
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${game.name}</h5>
                    <div class="card-text">
                        <div class="row mb-3">
                            <div class="col-6">
                                <div class="stats-label">TICKET COST</div>
                                <div class="stats-value">$${game.cost.toFixed(2)}</div>
                            </div>
                            <div class="col-6">
                                <div class="stats-label">OVERALL ODDS</div>
                                <div class="stats-value">1:${game.current_odds.toFixed(2)}</div>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-6">
                                <div class="stats-label">TOP PRIZE</div>
                                <div class="stats-value">$${game.jackpot.toLocaleString()}</div>
                            </div>
                            <div class="col-6">
                                <div class="stats-label">EXPECTED VALUE</div>
                                <span class="${game.net_ev >= 0 ? 'positive-ev' : 'negative-ev'} stats-value">
                                    $${game.net_ev.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>
                    <a href="game.html?game=${this.generateSlug(game.name)}" class="btn btn-primary w-100">
                        View Details
                    </a>
                </div>
            </div>
        </div>`;
    }

    generateSlug(name) {
        return name
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    updateDisplay() {
        const searchTerm = this.searchInput.value.toLowerCase();
        const sortType = this.sortSelect.value;

        let filtered = this.data.filter(game => 
            game.name.toLowerCase().includes(searchTerm)
        );

        filtered.sort((a, b) => {
            switch (sortType) {
                case 'ev':
                    return b.net_ev - a.net_ev;
                case 'cost':
                    return b.cost - a.cost;
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'odds':
                    return a.current_odds - b.current_odds;
                case 'jackpot':
                    return b.jackpot - a.jackpot;
                default:
                    return 0;
            }
        });

        this.gamesGrid.innerHTML = filtered.map(game => this.renderGameCard(game)).join('');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ScratcherAnalytics();
}); 