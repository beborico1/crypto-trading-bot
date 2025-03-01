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
function loadPerformanceChart(container) {
    const symbol = container.data('symbol');
    const chartId = `${symbol.replace('/', '-')}-chart`;
    const loadingSpinner = container.find('.chart-loading');
    const errorMessage = container.find('.chart-error-message');
    const chartElement = document.getElementById(chartId);

    if (!chartElement) return;

    loadingSpinner.show();
    errorMessage.hide();

    // Extract base and quote from symbol
    const [base, quote] = symbol.split('/');

    // Call the API for chart data
    $.ajax({
        url: `/performance_chart/${base}/${quote}`,
        type: 'GET',
        success: function (response) {
            loadingSpinner.hide();
            if (response.success && response.chart) {
                try {
                    const chartData = JSON.parse(response.chart);
                    Plotly.newPlot(chartId, chartData.data, chartData.layout, {
                        responsive: true,
                        displayModeBar: false
                    });
                    
                    // Make chart responsive
                    window.addEventListener('resize', function() {
                        Plotly.Plots.resize(chartElement);
                    });
                } catch (error) {
                    console.error('Error parsing chart JSON:', error);
                    errorMessage.find('.error-text').text('Error rendering chart: ' + error.message);
                    errorMessage.show();
                }
            } else {
                errorMessage.find('.error-text').text(response.message || 'Failed to load chart data');
                errorMessage.show();
            }
        },
        error: function (xhr, status, error) {
            loadingSpinner.hide();
            console.error('Chart loading error:', error, xhr.responseText);
            errorMessage.find('.error-text').text('Error loading chart: ' + (error || 'Server error'));
            errorMessage.show();
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