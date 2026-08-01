/**
 * =================================================================================
 * 통계 차트 JavaScript
 * - Chart.js 기반 통계 차트 렌더링
 * - 데이터는 <script id="stats-data" type="application/json"> 에서 로드
 * =================================================================================
 */

let charts = {};

/**
 * 차트 canvas 컨텍스트를 가져오고 기존 차트가 있으면 파괴.
 * @param {string} canvasId - canvas 엘리먼트 id
 * @param {string} key - charts 맵의 키 (예: 'dailyPie')
 * @returns {CanvasRenderingContext2D}
 */
/** CSS 토큰을 읽어 온다. 차트 색이 그리드 색과 달라 보이면 안 된다. */
function cssToken(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function prepareChart(canvasId, key) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (charts[key]) charts[key].destroy();
    return ctx;
}

/**
 * 데이터가 없을 때 canvas 중앙에 placeholder 문구를 그림.
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} [message='데이터가 없습니다']
 */
function drawEmptyState(ctx, message) {
    ctx.fillStyle = '#6c757d';
    if (!message) message = gettext('데이터가 없습니다');
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(message, ctx.canvas.width / 2, ctx.canvas.height / 2);
}

function initTabHashSync() {
    const tabsRoot = document.getElementById('statsTabs');
    if (!tabsRoot || !window.bootstrap) return;

    // 로드 시 URL hash에 해당하는 탭 활성화
    const hash = window.location.hash;
    if (hash) {
        const trigger = tabsRoot.querySelector('[data-bs-target="' + hash + '"]');
        if (trigger) {
            try { new bootstrap.Tab(trigger).show(); }
            catch (e) { console.error('탭 활성화 오류:', e); }
        }
    }

    // 탭 전환 시 hash 갱신 (reload 없이)
    tabsRoot.querySelectorAll('[data-bs-toggle="tab"]').forEach(function(btn) {
        btn.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            if (!target) return;
            history.replaceState(null, '', location.pathname + location.search + target);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initTabHashSync();

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
        renderHourlyBarChart(daily.hourly_stats, daily.tag_stats);
        renderWeeklyLineChart(weekly.tag_weekly_stats, weekly.weekly_data);
        renderWeeklyBarChart(weekly.weekly_data);
        renderMonthlyLineChart(monthly);
    } catch (error) {
        console.error('차트 렌더링 오류:', error);
    }
});

function renderHourlyBarChart(hourlyStats, tagStats) {
    const ctx = prepareChart('hourlyBarChart', 'hourlyBar');
    if (hourlyStats.every(hour => Object.keys(hour).length === 0)) {
        drawEmptyState(ctx);
        return;
    }

    const hours = Array.from({length: 24}, (_, i) => interpolate(gettext('%s:00'), [i]));

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
                            return interpolate(gettext('%s min'), [value]);
                        }
                    }
                }
            },
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return interpolate(
                                gettext('%(label)s: %(m)s min'),
                                {label: context.dataset.label || '', m: context.raw},
                                true
                            );
                        }
                    }
                }
            }
        }
    });
}

function renderWeeklyLineChart(tagStats, weeklyData) {
    const ctx = prepareChart('weeklyLineChart', 'weeklyLine');
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
    const ctx = prepareChart('weeklyBarChart', 'weeklyBar');
    charts.weeklyBar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: weeklyData.map(day => day.day_korean),
            datasets: [{
                label: gettext('Active hours'),
                data: weeklyData.map(day => day.total_hours),
                backgroundColor: cssToken('--color-accent-work'),
                borderWidth: 0,
                borderRadius: 3
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
    const ctx = prepareChart('monthlyLineChart', 'monthlyLine');
    if (!monthlyData || !monthlyData.tag_stats || monthlyData.tag_stats.length === 0) {
        drawEmptyState(ctx);
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
                x: { title: { display: true, text: gettext('Date') } },
                y: {
                    beginAtZero: true,
                    max: 24,
                    title: { display: true, text: gettext('Hours') },
                    ticks: {
                        callback: function(value) {
                            return interpolate(gettext('%sh'), [value]);
                        }
                    }
                }
            },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return interpolate(
                                gettext('%(label)s: %(h)sh'),
                                {label: context.dataset.label, h: context.parsed.y},
                                true
                            );
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

