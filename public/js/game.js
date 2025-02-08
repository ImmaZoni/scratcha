class GameDetails {
    constructor() {
        this.initializeElements();
        this.loadGameData();
    }

    initializeElements() {
        this.loading = document.getElementById('loading');
        this.content = document.getElementById('gameContent');
        this.gameName = document.getElementById('gameName');
        this.gameCost = document.getElementById('gameCost');
        this.gameOdds = document.getElementById('gameOdds');
        this.gameJackpot = document.getElementById('gameJackpot');
        this.gameEV = document.getElementById('gameEV');
        this.prizeTiers = document.getElementById('prizeTiers');
    }

    async loadGameData() {
        try {
            // Get game slug from URL
            const urlParams = new URLSearchParams(window.location.search);
            const gameSlug = urlParams.get('game');
            
            if (!gameSlug) {
                throw new Error('No game specified');
            }

            // Load game data
            const response = await fetch('./web_data/current_analysis.json');
            if (!response.ok) throw new Error('Failed to load game data');
            
            const games = await response.json();
            const game = games.find(g => this.generateSlug(g.name) === gameSlug);
            
            if (!game) {
                throw new Error('Game not found');
            }

            this.displayGame(game);
            
        } catch (error) {
            console.error('Error:', error);
            this.loading.innerHTML = `
                <div class="alert alert-danger">
                    ${error.message}
                </div>
            `;
        }
    }

    displayGame(game) {
        // Update page title
        document.title = `${game.name} - AZ Scratcher Analytics`;
        
        // Update main stats
        this.gameName.textContent = game.name;
        this.gameCost.textContent = `$${game.cost.toFixed(2)}`;
        this.gameOdds.textContent = `1:${game.current_odds.toFixed(2)}`;
        this.gameJackpot.textContent = `$${game.jackpot.toLocaleString()}`;
        
        const evClass = game.net_ev >= 0 ? 'positive-ev' : 'negative-ev';
        this.gameEV.className = `stats-value ${evClass}`;
        this.gameEV.textContent = `$${game.net_ev.toFixed(2)}`;

        // Display prize tiers
        this.displayPrizeTiers(game);
        
        // Create chart
        this.createPrizeChart(game);

        // Show content
        this.loading.style.display = 'none';
        this.content.style.display = 'block';
    }

    displayPrizeTiers(game) {
        const tiers = Object.entries(game.prize_tiers)
            .sort((a, b) => parseFloat(b[0]) - parseFloat(a[0]));

        // Helper function to format percentage with appropriate precision
        const formatPercentage = (value) => {
            if (value < 0.01) {
                return value.toFixed(6);
            } else if (value < 0.1) {
                return value.toFixed(4);
            } else if (value < 1) {
                return value.toFixed(3);
            }
            return value.toFixed(2);
        };

        this.prizeTiers.innerHTML = `
            <div class="col-12 mb-3">
                <div class="alert alert-info">
                    <strong>Note:</strong> Percentages shown represent the distribution of remaining winning tickets. 
                    The actual odds of winning any prize are 1 in ${game.current_odds.toFixed(2)} as stated on the ticket.
                    <br>
                    <small>Total tickets: ${game.ticket_data.total_tickets.toLocaleString()}, 
                    Remaining: ${game.ticket_data.remaining_tickets.toLocaleString()} 
                    (${game.ticket_data.percent_remaining.toFixed(1)}%)</small>
                </div>
            </div>
            ${tiers.map(([prize, data]) => `
                <div class="col-md-4">
                    <div class="card prize-tier">
                        <div class="card-body">
                            <div class="stats-label">PRIZE: $${parseFloat(prize).toLocaleString()}</div>
                            <div class="stats-value">${formatPercentage(data.percentage)}% of winning tickets</div>
                            <div class="small text-muted">
                                Remaining: ${data.remaining.toLocaleString()} / ${data.total.toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        `;
    }

    createPrizeChart(game) {
        const ctx = document.getElementById('prizeChart').getContext('2d');
        const prizes = Object.entries(game.prize_tiers)
            .sort((a, b) => parseFloat(b[0]) - parseFloat(a[0]));

        // Format tooltips to show full precision
        const tooltipFormat = (value) => {
            if (value < 0.01) return value.toFixed(6);
            if (value < 0.1) return value.toFixed(4);
            if (value < 1) return value.toFixed(3);
            return value.toFixed(2);
        };

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: prizes.map(([prize]) => `$${parseFloat(prize).toLocaleString()}`),
                datasets: [{
                    label: '% of Remaining Winning Tickets',
                    data: prizes.map(([, data]) => data.percentage),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.raw;
                                return `${tooltipFormat(value)}% of winning tickets`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Distribution of Remaining Winning Tickets'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '% of Winning Tickets'
                        },
                        ticks: {
                            callback: function(value) {
                                return tooltipFormat(value) + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    generateSlug(name) {
        return name
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new GameDetails();
}); 