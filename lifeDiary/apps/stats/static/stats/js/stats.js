/**
 * =================================================================================
 * 통계 차트 JavaScript
 * - Chart.js 기반 통계 차트 렌더링
 * - 데이터는 <script id="stats-data" type="application/json"> 에서 로드
 * =================================================================================
 */

let charts = {};

document.addEventListener('DOMContentLoaded', function() {
    function parseJsonScript(id) {
        const el = document.getElementById(id);
        if (!el) { console.error(id + ' 요소를 찾을 수 없습니다.'); return null; }
        try { return JSON.parse(el.textContent); }
        catch (e) { console.error(id + ' 파싱 오류:', e); return null; }
    }

    const daily = parseJsonScript('daily-stats-data');
    const weekly = parseJsonScript('weekly-stats-data');
    const monthly = parseJsonScript('monthly-stats-data');
    const tagAnalysis = parseJsonScript('tag-analysis-data');

    if (!daily || !weekly || !monthly || !tagAnalysis) {
        console.error('통계 데이터가 불완전합니다.');
        return;
    }

    try {
        renderDailyPieChart(daily.tag_stats);
        renderHourlyBarChart(daily.hourly_stats, daily.tag_stats);
        renderWeeklyLineChart(weekly.tag_weekly_stats, weekly.weekly_data);
        renderWeeklyBarChart(weekly.weekly_data);
        renderMonthlyLineChart(monthly);
        renderTagTotalChart(tagAnalysis);
    } catch (error) {
        console.error('차트 렌더링 오류:', error);
    }
});

function renderDailyPieChart(tagStats) {
    const ctx = document.getElementById('dailyPieChart').getContext('2d');

    if (charts.dailyPie) {
        charts.dailyPie.destroy();
    }

    if (tagStats.length === 0) {
        ctx.fillStyle = '#6c757d';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('데이터가 없습니다', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }

    charts.dailyPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: tagStats.map(tag => tag.name),
            datasets: [{
                data: tagStats.map(tag => tag.hours),
                backgroundColor: tagStats.map(tag => tag.color),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const hours = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((hours / total) * 100).toFixed(1);
                            return `${context.label}: ${hours}시간 (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderHourlyBarChart(hourlyStats, tagStats) {
    const ctx = document.getElementById('hourlyBarChart').getContext('2d');

    if (charts.hourlyBar) {
        charts.hourlyBar.destroy();
    }

    if (hourlyStats.every(hour => Object.keys(hour).length === 0)) {
        ctx.fillStyle = '#6c757d';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('데이터가 없습니다', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }

    const hours = Array.from({length: 24}, (_, i) => `${i}시`);

    const allTags = {};
    if (tagStats) {
        tagStats.forEach(tag => {
            allTags[tag.name] = tag.color;
        });
    }

    const datasets = Object.keys(allTags).map(tagName => {
        return {
            label: tagName,
            data: hourlyStats.map(hourData => hourData[tagName] || 0),
            backgroundColor: allTags[tagName],
        };
    });

    charts.hourlyBar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    max: 60,
                    ticks: {
                        callback: function(value) {
                            return value + '분';
                        }
                    }
                }
            },
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label || ''}: ${context.raw}분`;
                        }
                    }
                }
            }
        }
    });
}

function renderWeeklyLineChart(tagStats, weeklyData) {
    const ctx = document.getElementById('weeklyLineChart').getContext('2d');

    if (charts.weeklyLine) {
        charts.weeklyLine.destroy();
    }

    const days = weeklyData.map(day => day.day_korean);

    charts.weeklyLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days,
            datasets: tagStats.map(tag => ({
                label: tag.name,
                data: tag.daily_hours,
                borderColor: tag.color,
                backgroundColor: tag.color + '20',
                tension: 0.4,
                fill: false
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { position: 'top' }
            }
        }
    });
}

function renderWeeklyBarChart(weeklyData) {
    const ctx = document.getElementById('weeklyBarChart').getContext('2d');

    if (charts.weeklyBar) {
        charts.weeklyBar.destroy();
    }

    charts.weeklyBar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: weeklyData.map(day => day.day_korean),
            datasets: [{
                label: '활동 시간',
                data: weeklyData.map(day => day.total_hours),
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderMonthlyLineChart(monthlyData) {
    const ctx = document.getElementById('monthlyLineChart').getContext('2d');

    if (charts.monthlyLine) {
        charts.monthlyLine.destroy();
    }

    if (!monthlyData || !monthlyData.tag_stats || monthlyData.tag_stats.length === 0) {
        ctx.fillStyle = '#6c757d';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('데이터가 없습니다', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }

    charts.monthlyLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.day_labels,
            datasets: monthlyData.tag_stats.map(tag => ({
                label: tag.name,
                data: tag.daily_hours,
                borderColor: tag.color,
                backgroundColor: tag.color + '20',
                tension: 0.4,
                fill: false,
                pointRadius: 3,
                pointHoverRadius: 5
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: '날짜' } },
                y: {
                    beginAtZero: true,
                    max: 24,
                    title: { display: true, text: '시간 (시)' },
                    ticks: {
                        callback: function(value) {
                            return value + '시간';
                        }
                    }
                }
            },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y}시간`;
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

function renderTagTotalChart(tagAnalysis) {
    const ctx = document.getElementById('tagTotalChart').getContext('2d');

    if (charts.tagTotal) {
        charts.tagTotal.destroy();
    }

    const top10 = tagAnalysis.slice(0, 10);

    charts.tagTotal = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(tag => tag.name),
            datasets: [{
                label: '총 시간 (시간)',
                data: top10.map(tag => tag.total_hours),
                backgroundColor: top10.map(tag => tag.color),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
