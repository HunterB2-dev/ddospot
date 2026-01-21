// Profile page JS

function getIPFromPath() {
    const parts = window.location.pathname.split('/');
    return parts[parts.length - 1];
}

async function loadProfile() {
    const ip = getIPFromPath();
    document.getElementById('profile-ip').textContent = ip;
    try {
        const res = await fetch(`/api/profile/${encodeURIComponent(ip)}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to load profile');
        renderProfile(data);
    } catch (e) {
        console.error('Profile load failed:', e);
        const tbody = document.getElementById('profile-events-tbody');
        tbody.innerHTML = `<tr><td colspan="5" class="loading">Error: ${e.message}</td></tr>`;
    }
}

function renderProfile(profile) {
    document.getElementById('first-seen').textContent = formatDate(profile.first_seen);
    document.getElementById('last-seen').textContent = formatDate(profile.last_seen);
    document.getElementById('total-events').textContent = (profile.total_events || 0).toLocaleString();
    document.getElementById('rate').textContent = profile.rate || 0;
    document.getElementById('attack-type').textContent = profile.attack_type || 'Unknown';
    document.getElementById('avg-payload').textContent = (profile.avg_payload || 0) + ' B';
    document.getElementById('severity').textContent = profile.severity || 'Unknown';

    // Protocol chart
    const protocols = profile.protocols || [];
    const counts = {};
    protocols.forEach(p => counts[p] = (counts[p] || 0) + 1);
    const labels = Object.keys(counts);
    const values = Object.values(counts);

    const ctx = document.getElementById('profile-protocol-chart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: ['#ff3333','#ff6b6b','#ff9999','#ffcccc']
            }]
        },
        options: { responsive: true, maintainAspectRatio: true }
    });

    // Recent events
    const tbody = document.getElementById('profile-events-tbody');
    tbody.innerHTML = '';
    (profile.recent_events || []).forEach(ev => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDate(ev.timestamp)}</td>
            <td>${ev.port}</td>
            <td>${ev.protocol}</td>
            <td>${ev.size} B</td>
            <td>${ev.type}</td>
        `;
        tbody.appendChild(row);
    });

    if ((profile.recent_events || []).length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No recent events</td></tr>';
    }
}

function formatDate(str) {
    if (!str) return 'N/A';
    const d = new Date(str);
    return d.toLocaleString();
}

document.addEventListener('DOMContentLoaded', loadProfile);
