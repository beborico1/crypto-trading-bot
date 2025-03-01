/**
 * performance.js - Enhanced Chart Management for High Frequency Trading Bot
 * Handles chart creation, updates, UI interactions with dark mode support
 */

// Document ready handler - initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    loadAllCharts();
    
    // Apply formatting to performance values
    formatPerformanceValues();
    
    // Set up symbol select dropdown behavior
    initializeSymbolSelect();
    
    // Set up strategy selector behaviors
    initializeStrategySelector();
    
    // Set up interval sync (range and number input)
    initializeIntervalSync();
    
    // Set up custom tooltips
    initializeTooltips();
    
    // Set up quick actions
    initializeQuickActions();
    
    // Set up retry buttons
    setupRetryButtons();
    
    // Set up refresh button
    setupRefreshButton();
    
    // Handle start bot form submission
    setupStartBotForm();
});

// Load and render performance chart for a specific trading pair
function loadPerformanceChart(symbol) {
    // Find the chart container for this symbol
    const chartContainer = document.querySelector(`.performance-chart-container[data-symbol="${symbol}"]`);
    if (!chartContainer) return;

    const loadingSpinner = chartContainer.querySelector('.chart-loading');
    const errorMessage = chartContainer.querySelector('.chart-error-message');
    const chartId = `${symbol.replace('/', '-')}-chart`;
    const chartElement = document.getElementById(chartId);
    
    if (!chartElement) return;

    // Show loading spinner, hide any previous error
    if (loadingSpinner) loadingSpinner.style.display = 'block';
    if (errorMessage) errorMessage.style.display = 'none';

    // Clean symbol by splitting it into base/quote components
    const symbolParts = symbol.split('/');
    if (symbolParts.length !== 2) {
        if (errorMessage) {
            const errorText = errorMessage.querySelector('.error-text');
            if (errorText) errorText.textContent = 'Invalid symbol format';
            errorMessage.style.display = 'block';
        }
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        return;
    }

    const base = symbolParts[0];
    const quote = symbolParts[1];

    // Call API to get chart data using fetch
    fetch(`/performance_chart/${base}/${quote}`)
        .then(response => response.json())
        .then(data => {
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            
            if (data.success && data.chart) {
                try {
                    const chartData = JSON.parse(data.chart);
                    
                    // Add dark mode styling
                    if (!chartData.layout) chartData.layout = {};
                    
                    // Apply dark theme modifications with darker text
                    Object.assign(chartData.layout, {
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { 
                            family: 'Inter, system-ui, sans-serif',
                            color: '#000000'  // Changed from '#b0b0c0' to black
                        },
                        margin: {l: 50, r: 20, t: 40, b: 40},
                        xaxis: {
                            gridcolor: '#434359',
                            linecolor: '#434359',
                            zerolinecolor: '#6a3de8',
                            tickfont: {
                                color: '#000000'  // Explicit dark color for x-axis tick labels
                            }
                        },
                        yaxis: {
                            gridcolor: '#434359',
                            linecolor: '#434359',
                            zerolinecolor: '#6a3de8',
                            tickprefix: '$',
                            zeroline: true,
                            tickfont: {
                                color: '#000000'  // Explicit dark color for y-axis tick labels
                            }
                        },
                        legend: {
                            bgcolor: 'rgba(0,0,0,0)',
                            font: {
                                color: '#000000'  // Dark color for legend text
                            }
                        },
                        height: 350,
                        autosize: true
                    });
                    
                    // Set title color if it exists
                    if (chartData.layout.title) {
                        if (typeof chartData.layout.title === 'string') {
                            chartData.layout.title = {
                                text: chartData.layout.title,
                                font: {
                                    color: '#e0e0e0'
                                }
                            };
                        } else {
                            chartData.layout.title.font = {
                                color: '#e0e0e0'
                            };
                        }
                    }
                    
                    // Update data colors if needed
                    if (chartData.data && chartData.data.length > 0) {
                        // Main line should be purple
                        if (chartData.data[0]) {
                            chartData.data[0].line = {
                                color: '#9266ff',
                                width: 3
                            };
                            
                            // Add area fill for nicer appearance
                            chartData.data[0].fill = 'tozeroy';
                            chartData.data[0].fillcolor = 'rgba(146, 102, 255, 0.1)';
                            
                            // Set proper hover template
                            chartData.data[0].hovertemplate = '%{y:.2f} USDT<br>%{x}<extra></extra>';
                        }
                        
                        // Buy markers should be green
                        if (chartData.data[1]) {
                            chartData.data[1].marker = chartData.data[1].marker || {};
                            chartData.data[1].marker.color = '#38d39f';
                        }
                        
                        // Sell markers should be red
                        if (chartData.data[2]) {
                            chartData.data[2].marker = chartData.data[2].marker || {};
                            chartData.data[2].marker.color = '#e53935';
                        }
                    }
                    
                    // Ensure y-axis shows starting point properly
                    if (chartData.data && chartData.data[0] && chartData.data[0].y && chartData.data[0].y.length > 0) {
                        const yData = chartData.data[0].y;
                        const minValue = Math.min(...yData);
                        const maxValue = Math.max(...yData);
                        const startValue = yData[0];
                        
                        // Set a baseline around the starting value for better visualization
                        const range = maxValue - minValue;
                        chartData.layout.yaxis.range = [
                            startValue - (range * 0.1), // 10% padding below
                            startValue + (range * 1.1)  // 10% padding above max
                        ];
                    }
                    
                    // Create the plot with responsive config
                    Plotly.newPlot(chartElement, chartData.data, chartData.layout, {
                        displayModeBar: false,
                        responsive: true
                    });
                    
                    // Handle window resize to ensure chart stays responsive
                    window.addEventListener('resize', function() {
                        Plotly.relayout(chartId, {
                            autosize: true
                        });
                    });
                } catch (error) {
                    console.error('Error parsing chart JSON:', error);
                    if (errorMessage) {
                        const errorText = errorMessage.querySelector('.error-text');
                        if (errorText) errorText.textContent = 'Error rendering chart: ' + error.message;
                        errorMessage.style.display = 'block';
                    }
                }
            } else {
                if (errorMessage) {
                    const errorText = errorMessage.querySelector('.error-text');
                    if (errorText) errorText.textContent = data.message || 'Failed to load chart data';
                    errorMessage.style.display = 'block';
                }
            }
        })
        .catch(error => {
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (errorMessage) {
                const errorText = errorMessage.querySelector('.error-text');
                if (errorText) errorText.textContent = 'Error loading chart: ' + (error.message || 'Server error');
                errorMessage.style.display = 'block';
            }
        });
}

// Apply color styling to performance values
function formatPerformanceValues() {
    // Process all elements with performance data attributes
    document.querySelectorAll('[data-performance-value]').forEach(function(element) {
        const value = parseFloat(element.dataset.performanceValue || 0);
        const isPercentage = element.dataset.isPercentage === 'true';

        // Remove existing color classes
        element.classList.remove(
            'performance-positive', 'performance-negative', 
            'performance-neutral', 'text-success', 
            'text-danger', 'text-info'
        );

        // Apply appropriate class and format
        if (value > 0) {
            element.classList.add('performance-positive', 'text-success');
            element.textContent = `+${value.toFixed(2)}${isPercentage ? '%' : ''}`;
        } else if (value < 0) {
            element.classList.add('performance-negative', 'text-danger');
            element.textContent = `${value.toFixed(2)}${isPercentage ? '%' : ''}`;
        } else {
            element.classList.add('performance-neutral', 'text-info');
            element.textContent = `0.00${isPercentage ? '%' : ''}`;
        }
    });

    // Process all profit/loss values
    document.querySelectorAll('[data-profit-value]').forEach(function(element) {
        const value = parseFloat(element.dataset.profitValue || 0);

        // Remove existing color classes
        element.classList.remove(
            'performance-positive', 'performance-negative', 
            'performance-neutral', 'text-success', 
            'text-danger', 'text-info'
        );

        // Apply appropriate class and format
        if (value > 0) {
            element.classList.add('performance-positive', 'text-success');
            element.textContent = `+$${value.toFixed(2)}`;
        } else if (value < 0) {
            element.classList.add('performance-negative', 'text-danger');
            element.textContent = `-$${Math.abs(value).toFixed(2)}`;
        } else {
            element.classList.add('performance-neutral', 'text-info');
            element.textContent = `$0.00`;
        }
    });
}

// Load all performance charts on the page
function loadAllCharts() {
    document.querySelectorAll('.performance-chart-container').forEach(function(container) {
        const symbol = container.dataset.symbol;
        if (symbol) {
            loadPerformanceChart(symbol);
        }
    });
    
    // Also format all performance values
    formatPerformanceValues();
}

// Set up retry buttons
function setupRetryButtons() {
    document.querySelectorAll('.btn-retry').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const container = this.closest('.performance-chart-container');
            const symbol = container.dataset.symbol;
            if (symbol) {
                loadPerformanceChart(symbol);
            }
        });
    });
}

// Set up refresh button
function setupRefreshButton() {
    const refreshButton = document.getElementById('refresh-performance');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            loadAllCharts();
        });
    }
    
    // Dashboard refresh button
    const dashboardRefreshButton = document.getElementById('refresh-dashboard');
    if (dashboardRefreshButton) {
        dashboardRefreshButton.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-sync-alt fa-spin me-1"></i> Refreshing...';
            
            setTimeout(() => {
                window.location.reload();
            }, 500);
        });
    }
}

// Initialize symbol select dropdown with search and custom option
function initializeSymbolSelect() {
    // Handle symbol select in start bot modal
    const symbolSelect = document.getElementById('symbol');
    const customSymbolInput = document.getElementById('custom-symbol');
    const assetSymbolSpan = document.querySelector('.asset-symbol');
    
    if (symbolSelect) {
        // Show/hide custom input field when "custom" option is selected
        symbolSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                if (customSymbolInput) {
                    customSymbolInput.classList.remove('d-none');
                    customSymbolInput.focus();
                }
            } else {
                if (customSymbolInput) {
                    customSymbolInput.classList.add('d-none');
                }
                
                // Update asset symbol in UI
                if (this.value && assetSymbolSpan) {
                    const baseCurrency = this.value.split('/')[0];
                    assetSymbolSpan.textContent = baseCurrency;
                }
            }
        });
        
        // Handle custom symbol input
        if (customSymbolInput) {
            customSymbolInput.addEventListener('blur', function() {
                if (this.value.trim() !== '' && symbolSelect.value === 'custom' && assetSymbolSpan) {
                    // Update asset symbol in UI based on custom input
                    const symbolParts = this.value.trim().split('/');
                    if (symbolParts.length > 0) {
                        assetSymbolSpan.textContent = symbolParts[0];
                    }
                }
            });
        }
        
        // Initialize Select2 for enhanced dropdown if available
        if (typeof $ !== 'undefined' && typeof $.fn.select2 !== 'undefined') {
            $(symbolSelect).select2({
                theme: 'bootstrap-5',
                dropdownParent: $('#startBotModal'),
                placeholder: 'Select a trading pair',
                allowClear: true
            });
        }
    }
}

// Initialize strategy selector with descriptions
function initializeStrategySelector() {
    const strategySelect = document.getElementById('strategy');
    const strategyDescription = document.querySelector('.strategy-description');
    
    if (strategySelect && strategyDescription) {
        // Strategy descriptions
        const descriptions = {
            'high_frequency': 'Ultra-fast trading with quick position entries/exits based on EMA crosses',
            'scalping': 'Short-term positions capturing small price movements with minimal risk',
            'enhanced': 'Combined technical indicators for more reliable entry/exit signals',
            'standard': 'Classic moving average crossover strategy for trending markets'
        };
        
        // Update description when strategy changes
        strategySelect.addEventListener('change', function() {
            if (descriptions[this.value]) {
                strategyDescription.textContent = descriptions[this.value];
            }
        });
        
        // Set initial description
        if (descriptions[strategySelect.value]) {
            strategyDescription.textContent = descriptions[strategySelect.value];
        }
    }
}

// Sync range and number inputs for interval
function initializeIntervalSync() {
    const intervalRange = document.getElementById('interval-range');
    const intervalInput = document.getElementById('interval');
    
    if (intervalRange && intervalInput) {
        // Sync range to input
        intervalRange.addEventListener('input', function() {
            intervalInput.value = this.value;
        });
        
        // Sync input to range
        intervalInput.addEventListener('input', function() {
            intervalRange.value = this.value;
        });
    }
}

// Initialize custom tooltips
function initializeTooltips() {
    // Use Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Initialize quick actions for the dashboard
function initializeQuickActions() {
    // Handle stop bot buttons
    document.querySelectorAll('.stop-bot').forEach(function(button) {
        button.addEventListener('click', function() {
            const symbol = this.dataset.symbol;
            if (!symbol) return;
            
            // Confirm before stopping
            if (confirm(`Are you sure you want to stop the bot for ${symbol}?`)) {
                fetch(`/stop_bot/${symbol}`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast(`Bot for ${symbol} stopped successfully.`, 'success');
                        // Reload after a short delay
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        showToast(data.message || 'Failed to stop bot.', 'error');
                    }
                })
                .catch(error => {
                    showToast(`Error stopping bot: ${error.message}`, 'error');
                });
            }
        });
    });
    
    // Generate dashboards button
    const generateButton = document.getElementById('generate-dashboards');
    if (generateButton) {
        generateButton.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-cog fa-spin me-1"></i> Generating...';
            
            fetch('/generate_dashboards', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Dashboards generated successfully.', 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(data.message || 'Failed to generate dashboards.', 'error');
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-chart-area me-1"></i> Generate Dashboards';
                }
            })
            .catch(error => {
                showToast(`Error generating dashboards: ${error.message}`, 'error');
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-chart-area me-1"></i> Generate Dashboards';
            });
        });
    }
}

// Helper function to show toast messages
function showToast(message, type = 'success') {
    // Don't proceed if Bootstrap is not available
    if (typeof bootstrap === 'undefined') {
        console.log(message);
        return;
    }
    
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create unique ID for this toast
    const toastId = `toast-${Date.now()}`;
    
    // Create toast element
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${type === 'success' ? 'bg-success' : 'bg-danger'} text-white">
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <small>just now</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Remove the toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Handle start bot form submission
function setupStartBotForm() {
    const startBotForm = document.getElementById('start-bot-form');
    const startBotButton = document.getElementById('start-bot-button');
    
    if (startBotForm && startBotButton) {
        startBotButton.addEventListener('click', function() {
            // Get symbol from either select or custom input
            const symbolSelect = document.getElementById('symbol');
            const customSymbolInput = document.getElementById('custom-symbol');
            let symbol = '';
            
            if (symbolSelect.value === 'custom' && customSymbolInput && customSymbolInput.value.trim() !== '') {
                symbol = customSymbolInput.value.trim();
            } else if (symbolSelect.value !== 'custom' && symbolSelect.value !== '') {
                symbol = symbolSelect.value;
            } else {
                showToast('Please select or enter a valid trading pair', 'error');
                return;
            }
            
            // Create form data for submission
            const formData = new FormData(startBotForm);
            
            // Override symbol if using custom
            if (symbolSelect.value === 'custom') {
                formData.set('symbol', symbol);
            }
            
            // Disable button during submission
            startBotButton.disabled = true;
            startBotButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Starting...';
            
            // Submit the form
            fetch('/start_bot', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Close modal
                    if (typeof bootstrap !== 'undefined') {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('startBotModal'));
                        if (modal) {
                            modal.hide();
                        }
                    }
                    
                    // Reload page after a short delay
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(data.message || 'Failed to start bot', 'error');
                    startBotButton.disabled = false;
                    startBotButton.innerHTML = '<i class="fas fa-play me-1"></i> Start Bot';
                }
            })
            .catch(error => {
                showToast(`Error starting bot: ${error.message}`, 'error');
                startBotButton.disabled = false;
                startBotButton.innerHTML = '<i class="fas fa-play me-1"></i> Start Bot';
            });
        });
    }
}