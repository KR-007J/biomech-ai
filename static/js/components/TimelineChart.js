/**
 * TimelineChart Component
 * Visualizes joint angles frame-by-frame
 */
export const TimelineChart = (canvasId, timeSeries) => {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Extract labels and data
    const labels = timeSeries.map(f => `${f.timestamp}s`);
    const kneeData = timeSeries.map(f => (f.angles.left_knee + f.angles.right_knee) / 2);
    const hipData = timeSeries.map(f => (f.angles.left_hip + f.angles.right_hip) / 2);

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Avg Knee Angle',
                    data: kneeData,
                    borderColor: '#00ffcc',
                    backgroundColor: 'rgba(0, 255, 204, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Avg Hip Angle',
                    data: hipData,
                    borderColor: '#a78bfa',
                    backgroundColor: 'rgba(167, 139, 250, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b', maxRotation: 0 }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b' },
                    min: 0,
                    max: 180
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', boxWidth: 10, font: { size: 10 } }
                }
            }
        }
    });
};
