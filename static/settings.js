// Settings Page JavaScript (Feature #11)

const API_BASE = '/api';
const API_KEY = localStorage.getItem('api_key') || 'demo-admin-key';

// ============= Tab Navigation =============

document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        switchTab(tabName);
    });
});

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Deactivate all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Activate button
    const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }

    // Load config for this tab
    loadTabConfig(tabName);
}

// ============= Configuration Loading =============

async function loadTabConfig(tabName) {
    try {
        let endpoint = '';
        let formId = '';

        switch(tabName) {
            case 'honeypot':
                endpoint = '/api/config/honeypot';
                formId = 'honeypot-form';
                break;
            case 'alerts':
                endpoint = '/api/config/alerts';
                formId = 'alerts-form';
                break;
            case 'responses':
                endpoint = '/api/config/responses';
                formId = 'responses-form';
                break;
            case 'system':
                endpoint = '/api/config/system';
                formId = 'system-form';
                break;
        }

        if (!endpoint) return;

        const response = await fetch(endpoint, {
            headers: { 'X-API-Key': API_KEY }
        });

        if (!response.ok) {
            console.error(`Failed to load ${tabName} config: ${response.status}`);
            return;
        }

        const data = await response.json();
        if (data.success && data.config) {
            populateForm(formId, data.config);
        }
    } catch (error) {
        console.error(`Error loading ${tabName} config:`, error);
        showMessage(`Error loading ${tabName} configuration`, 'error');
    }
}

function populateForm(formId, config) {
    const form = document.getElementById(formId);
    if (!form) return;

    for (const [key, value] of Object.entries(config)) {
        const field = form.elements[key];
        if (!field) continue;

        if (field.type === 'checkbox') {
            field.checked = value === true || value === 'true' || value === 1;
        } else {
            field.value = value;
        }
    }
}

// ============= Form Submission =============

document.getElementById('honeypot-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    submitConfig('honeypot', e.target);
});

document.getElementById('alerts-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    submitConfig('alerts', e.target);
});

document.getElementById('responses-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    submitConfig('responses', e.target);
});

document.getElementById('system-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    submitConfig('system', e.target);
});

async function submitConfig(tabName, form) {
    try {
        const formData = new FormData(form);
        const config = {};

        for (const [key, value] of formData.entries()) {
            if (form.elements[key].type === 'checkbox') {
                config[key] = form.elements[key].checked;
            } else {
                config[key] = value;
            }
        }

        const endpoint = `/api/config/${tabName}`;
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showMessage(`${tabName} configuration saved successfully!`, 'success', tabName);
        } else {
            showMessage(`Error saving ${tabName} configuration: ${data.error || 'Unknown error'}`, 'error', tabName);
        }
    } catch (error) {
        console.error(`Error submitting ${tabName} config:`, error);
        showMessage(`Error saving ${tabName} configuration`, 'error', tabName);
    }
}

// ============= Message Display =============

function showMessage(message, type, tabName) {
    const messageEl = document.getElementById(`${tabName}-status-msg`);
    if (!messageEl) return;

    messageEl.textContent = message;
    messageEl.className = `status-message ${type}`;

    // Auto-hide success messages
    if (type === 'success') {
        setTimeout(() => {
            messageEl.textContent = '';
            messageEl.className = 'status-message';
        }, 3000);
    }
}

// ============= Test Functions =============

document.getElementById('test-alert-btn')?.addEventListener('click', async () => {
    try {
        showMessage('Sending test alert...', 'loading', 'alerts');

        const response = await fetch(`${API_BASE}/alerts/test`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: 'Test Alert',
                message: 'This is a test alert from DDoSPot settings'
            })
        });

        if (response.ok) {
            showMessage('Test alert sent successfully!', 'success', 'alerts');
        } else {
            showMessage('Failed to send test alert', 'error', 'alerts');
        }
    } catch (error) {
        console.error('Error sending test alert:', error);
        showMessage('Error sending test alert', 'error', 'alerts');
    }
});

document.getElementById('test-webhook-btn')?.addEventListener('click', async () => {
    try {
        const webhookUrl = document.getElementById('webhook_url')?.value;

        if (!webhookUrl) {
            showMessage('Please enter a webhook URL first', 'error', 'responses');
            return;
        }

        showMessage('Testing webhook...', 'loading', 'responses');

        const response = await fetch(`${API_BASE}/config/test/webhook`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                webhook_url: webhookUrl
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showMessage('Webhook test successful!', 'success', 'responses');
        } else {
            showMessage(`Webhook test failed: ${data.error || 'Unknown error'}`, 'error', 'responses');
        }
    } catch (error) {
        console.error('Error testing webhook:', error);
        showMessage('Error testing webhook', 'error', 'responses');
    }
});

document.getElementById('restart-services-btn')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to restart the services? This may cause temporary downtime.')) {
        return;
    }

    try {
        showMessage('Restarting services...', 'loading', 'system');

        const response = await fetch(`${API_BASE}/config/restart`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showMessage('Services restart scheduled!', 'success', 'system');
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showMessage(`Error restarting services: ${data.error || 'Unknown error'}`, 'error', 'system');
        }
    } catch (error) {
        console.error('Error restarting services:', error);
        showMessage('Error restarting services', 'error', 'system');
    }
});

// ============= Service Status Display =============

async function loadServiceStatus() {
    try {
        const response = await fetch(`${API_BASE}/status/health`, {
            headers: { 'X-API-Key': API_KEY }
        });

        if (!response.ok) return;

        const data = await response.json();
        const statusContainer = document.getElementById('honeypot-status');

        if (!statusContainer) return;

        let html = '';

        // Honeypot service status
        if (data.status === 'healthy') {
            html += `
                <div class="status-indicator running">
                    <div class="status-badge"></div>
                    <div class="status-text">
                        <div class="status-label">System Status</div>
                        <div class="status-value">Healthy</div>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="status-indicator stopped">
                    <div class="status-badge"></div>
                    <div class="status-text">
                        <div class="status-label">System Status</div>
                        <div class="status-value">Degraded</div>
                    </div>
                </div>
            `;
        }

        // Event count
        html += `
            <div class="status-indicator">
                <div class="status-text">
                    <div class="status-label">Total Events</div>
                    <div class="status-value">${data.event_count || 0}</div>
                </div>
            </div>
        `;

        // Database status
        html += `
            <div class="status-indicator ${data.database === 'connected' ? 'running' : 'stopped'}">
                <div class="status-badge"></div>
                <div class="status-text">
                    <div class="status-label">Database</div>
                    <div class="status-value">${data.database || 'Unknown'}</div>
                </div>
            </div>
        `;

        statusContainer.innerHTML = html;
    } catch (error) {
        console.error('Error loading service status:', error);
    }
}

// ============= Initialization =============

document.addEventListener('DOMContentLoaded', () => {
    // Load initial tab
    switchTab('honeypot');

    // Load service status
    loadServiceStatus();

    // Refresh service status every 30 seconds
    setInterval(loadServiceStatus, 30000);

    // Show welcome message
    console.log('DDoSPot Settings Page (Feature #11) loaded');
});

// ============= Form Validation =============

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    let isValid = true;

    // Validate number fields
    form.querySelectorAll('input[type="number"]').forEach(input => {
        if (input.value && input.min && parseInt(input.value) < parseInt(input.min)) {
            input.classList.add('error');
            isValid = false;
        } else if (input.value && input.max && parseInt(input.value) > parseInt(input.max)) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
    });

    // Validate URL fields
    form.querySelectorAll('input[type="url"]').forEach(input => {
        if (input.value) {
            try {
                new URL(input.value);
                input.classList.remove('error');
            } catch {
                input.classList.add('error');
                isValid = false;
            }
        }
    });

    return isValid;
}

// Add form submit validation
document.querySelectorAll('.settings-form').forEach(form => {
    form.addEventListener('submit', (e) => {
        if (!validateForm(form.id)) {
            e.preventDefault();
            showMessage('Please fix the errors in the form', 'error');
        }
    });
});

// ============= Keyboard Shortcuts =============

document.addEventListener('keydown', (e) => {
    // Ctrl+S or Cmd+S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const form = document.querySelector('.tab-content.active form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }

    // Esc to reset
    if (e.key === 'Escape') {
        const form = document.querySelector('.tab-content.active form');
        if (form) {
            form.reset();
        }
    }
});

// ============= Storage Management =============

// Save API key to localStorage for convenience
function saveApiKey(key) {
    localStorage.setItem('api_key', key);
}

// Get API key from localStorage
function getApiKey() {
    return localStorage.getItem('api_key') || 'demo-admin-key';
}
