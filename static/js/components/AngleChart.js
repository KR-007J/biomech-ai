/**
 * AngleChart Component
 * Visualizes joint angles over time or as a summary
 */
export const AngleChart = (canvasId, data) => {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['L-Knee', 'R-Knee', 'L-Elbow', 'R-Elbow', 'L-Hip', 'R-Hip'],
            datasets: [{
                label: 'Movement Range (Avg Degrees)',
                data: [
                    data.left_knee_angle || 0,
                    data.right_knee_angle || 0,
                    data.left_elbow_angle || 0,
                    data.right_elbow_angle || 0,
                    data.left_hip_angle || 0,
                    data.right_hip_angle || 0
                ],
                backgroundColor: 'rgba(0, 255, 204, 0.2)',
                borderColor: '#00ffcc',
                pointBackgroundColor: '#00ffcc',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#00ffcc'
            }]
        },
        options: {
            elements: { line: { borderWidth: 3 } },
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: { color: '#94a3b8' },
                    ticks: { display: false, max: 180, stepSize: 30 }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
};
