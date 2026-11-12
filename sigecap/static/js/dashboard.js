document.addEventListener('DOMContentLoaded', function () {
    const read = id => JSON.parse(document.getElementById(id).textContent);
    const trend = document.getElementById('trendChart');
    if (trend) {
        new Chart(trend, {
            type: 'line',
            data: {
                labels: read('dashboard-trend-labels'),
                datasets: [
                    {
                        label: 'Participaciones con asistencia o aprobación',
                        data: read('dashboard-trend-participaciones'),
                        borderColor: '#0051d5', backgroundColor: 'rgba(0, 81, 213, 0.08)',
                        fill: true, tension: 0.35, borderWidth: 2.5, pointRadius: 4
                    },
                    {
                        label: 'Formaciones en curso o finalizadas',
                        data: read('dashboard-trend-formaciones'),
                        borderColor: '#059669', backgroundColor: 'rgba(5, 150, 105, 0.08)',
                        tension: 0.35, borderWidth: 2.5, pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
    const area = document.getElementById('areaChart');
    if (area) {
        new Chart(area, {
            type: 'doughnut',
            data: {
                labels: read('dashboard-area-labels'),
                datasets: [{
                    data: read('dashboard-area-values'),
                    backgroundColor: ['#00236f', '#0051d5', '#316bf3', '#60a5fa', '#93c5fd'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '70%',
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } }
            }
        });
    }
});
