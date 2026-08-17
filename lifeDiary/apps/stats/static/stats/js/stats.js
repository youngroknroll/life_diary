/**
 * =================================================================================
 * 통계 차트 JavaScript
 * - Chart.js 기반 통계 차트 렌더링, 데이터 단위는 태그가 아니라 카테고리 5개
 * - 데이터는 <script id="*-stats-data" type="application/json"> 에서 로드
 * =================================================================================
 */

let charts = {};
let chartRethemeHandlers = [];
let categoryNames = {};

/** CSS 토큰을 읽어 온다. 차트 색이 그리드 색과 달라 보이면 안 된다. */
function cssToken(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function isDarkTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

function isMobileViewport() {
    return window.matchMedia('(max-width: 767.98px)').matches;
}

function prepareChart(canvasId, key) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    if (charts[key]) charts[key].destroy();
    return ctx;
}

// 카테고리 5색. 면(파스텔)은 기존 --color-accent-* 토큰, 선(딥)은 신규 —
// 흰 배경에서 파스텔 선은 대비 1.4~2.2로 안 보인다. 다크 모드는 파스텔
// 원색을 그대로 선에 쓴다(대비 7.8~11.6) — categoryLineColor가 분기한다.
// 딥 값은 짝이 되는 면의 색상(hue)을 그대로 따라가야 한다 — 어긋나면 같은
// 카테고리가 표와 그래프에서 다른 색으로 읽힌다. 대비는 3.6~3.9로 맞춘다.
// category_keys.py의 CATEGORY_LINE_COLOR와 같은 값이어야 한다.
const CATEGORY_ORDER = ['work', 'move', 'care', 'sleep', 'life'];
const CATEGORY_LINE = {
    work: '#4E8F63', move: '#4F8B9E', care: '#C1715A', life: '#A87A1A', sleep: '#8A78D0',
};
const CATEGORY_FILL_TOKEN = {
    work: '--color-accent-work', move: '--color-accent-move', care: '--color-accent-care',
    life: '--color-accent-rest', sleep: '--color-accent-sleep',
};

function categoryLineColor(key) {
    return isDarkTheme() ? cssToken(CATEGORY_FILL_TOKEN[key]) : CATEGORY_LINE[key];
}

function categoryFillColor(key) {
    return cssToken(CATEGORY_FILL_TOKEN[key]);
}

function categoryName(key) {
    return categoryNames[key] || key;
}

function applyChartTheme() {
    Chart.defaults.color = cssToken('--color-text-meta');
    Chart.defaults.font.family = cssToken('--font-body');
    Chart.defaults.font.size = 11;
    Chart.defaults.borderColor = cssToken('--color-border-soft');
}

/** 테마가 바뀌면 각 차트의 명시적 색(기본값으로 안 잡히는 것들)을 다시
 * 계산해 update('none')한다. */
function rethemeCharts() {
    applyChartTheme();
    chartRethemeHandlers.forEach(function (fn) { fn(); });
}

/** 테마 전환은 커스텀 이벤트를 쏘지 않는다. base.html 은 <html data-theme> 만
 * 바꾸므로 그 속성을 직접 관찰한다 — 헤더 메뉴 클릭과 시스템 테마 변경을
 * 모두 잡고, 컨트롤의 id 가 바뀌어도 다시 끊기지 않는다. */
function observeThemeChanges() {
    new MutationObserver(rethemeCharts).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme'],
    });
}

function isCategoryDataEmpty(categoryStats) {
    return !categoryStats || categoryStats.every(function (c) { return c.total_hours === 0; });
}

function toggleChartEmptyState(canvas, emptyEl, legendEl, isEmpty) {
    if (canvas) canvas.hidden = isEmpty;
    if (emptyEl) emptyEl.hidden = !isEmpty;
    if (legendEl) legendEl.hidden = isEmpty;
}

/**
 * 카테고리 칩 범례를 그린다. 클릭하면 해당 데이터셋을 토글하고 취소선을 켠다.
 * datasetIndex는 항상 CATEGORY_ORDER 안에서의 위치와 같다 — buildDatasets가
 * 그 순서로 데이터셋을 만들기 때문이다.
 */
function buildCategoryLegend(container, chart) {
    if (!container) return;
    container.innerHTML = '';

    CATEGORY_ORDER.forEach(function (key, datasetIndex) {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'chart-legend__item';
        // 표시 상태는 차트에서 읽는다 — 상수로 다시 칠하면 테마 전환으로
        // 범례를 다시 그릴 때 사용자가 끈 선이 켜진 것처럼 보인다.
        item.classList.toggle('is-off', !chart.isDatasetVisible(datasetIndex));
        const swatch = document.createElement('span');
        swatch.className = 'chart-legend__swatch';
        swatch.style.backgroundColor = categoryLineColor(key);
        item.appendChild(swatch);
        item.appendChild(document.createTextNode(categoryName(key)));
        item.addEventListener('click', function () {
            const nowVisible = !chart.isDatasetVisible(datasetIndex);
            chart.setDatasetVisibility(datasetIndex, nowVisible);
            item.classList.toggle('is-off', !nowVisible);
            chart.update();
        });
        container.appendChild(item);
    });
}

/** 툴팁 배경은 --color-text(라이트=검정, 다크=흰색)라, 글자는 반드시 그 반대인
 * --color-surface 로 못박는다. 지정하지 않으면 Chart.defaults.color(회색)가
 * 쓰여 다크 모드에서 흰 배경에 회색 글자가 되어 읽히지 않는다. */
function tooltipBaseOptions() {
    const ink = cssToken('--color-surface');
    return {
        backgroundColor: cssToken('--color-text'),
        titleColor: ink,
        bodyColor: ink,
        titleFont: { family: cssToken('--font-mono') },
        bodyFont: { family: cssToken('--font-mono') },
        itemSort: function (a, b) { return b.parsed.y - a.parsed.y; },
    };
}

function initTabHashSync() {
    const tabsRoot = document.getElementById('statsTabs');
    if (!tabsRoot || !window.bootstrap) return;

    // 탭 전환 시 hash 갱신(reload 없이) + .segmented__item의 is-active 동기화.
    // Bootstrap Tab이 자체 "active" 클래스는 관리하지만 이 프로젝트의 세그먼트
    // 스타일은 is-active를 본다 — nav-tabs를 걷어내며 생긴 차이라 여기서 잇는다.
    // 리스너를 먼저 붙이고 나서 아래 hash 활성화를 해야 한다 — 순서가 바뀌면
    // 로드 시 hash가 쏘는 첫 shown.bs.tab을 놓쳐 pill만 요약에 남는다.
    const tabTriggers = tabsRoot.querySelectorAll('[data-bs-toggle="tab"]');
    tabTriggers.forEach(function(btn) {
        btn.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target) {
                history.replaceState(null, '', location.pathname + location.search + target);
            }
            tabTriggers.forEach(function(t) { t.classList.toggle('is-active', t === e.target); });
        });
    });

    // 로드 시 URL hash에 해당하는 탭 활성화
    const hash = window.location.hash;
    if (hash) {
        const trigger = tabsRoot.querySelector('[data-bs-target="' + hash + '"]');
        if (trigger) {
            try { new bootstrap.Tab(trigger).show(); }
            catch (e) { console.error('탭 활성화 오류:', e); }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    applyChartTheme();
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

    (weekly.category_stats || []).forEach(function (c) { categoryNames[c.key] = c.name; });

    try {
        renderHourlyBarChart(daily.hourly_stats);
        renderWeeklyLineChart(weekly.category_stats, weekly.weekly_data);
        renderWeeklyBarChart(weekly.weekly_data);
        renderMonthlyLineChart(monthly);
    } catch (error) {
        console.error('차트 렌더링 오류:', error);
    }

    observeThemeChanges();
});

function renderHourlyBarChart(hourlyStats) {
    const canvas = document.getElementById('hourlyBarChart');
    const emptyEl = document.getElementById('hourlyBarEmpty');
    const isEmpty = !hourlyStats || hourlyStats.every(function (hour) { return Object.keys(hour).length === 0; });
    toggleChartEmptyState(canvas, emptyEl, null, isEmpty);
    if (isEmpty) return;

    const ctx = prepareChart('hourlyBarChart', 'hourlyBar');
    const hours = Array.from({length: 24}, (_, i) => interpolate(gettext('%s:00'), [i]));
    const shownHourTicks = [0, 6, 12, 18, 23];

    const datasets = CATEGORY_ORDER.map(function (key) {
        return {
            label: categoryName(key),
            data: hourlyStats.map(function (hourData) { return hourData[key] || 0; }),
            backgroundColor: categoryFillColor(key),
            borderWidth: 0,
        };
    });

    charts.hourlyBar = new Chart(ctx, {
        type: 'bar',
        data: { labels: hours, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    ticks: {
                        autoSkip: false,
                        callback: function (val, idx) {
                            return shownHourTicks.includes(idx) ? hours[idx] : '';
                        },
                    },
                },
                y: {
                    stacked: true,
                    min: 0,
                    max: 60,
                    ticks: {
                        stepSize: 30,
                        callback: function(value) {
                            return interpolate(gettext('%s min'), [value]);
                        }
                    },
                    grid: { color: cssToken('--color-border-soft') },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: Object.assign(tooltipBaseOptions(), {
                    callbacks: {
                        label: function(context) {
                            return interpolate(
                                gettext('%(label)s: %(m)s min'),
                                {label: context.dataset.label || '', m: context.raw},
                                true
                            );
                        }
                    }
                })
            }
        }
    });

    chartRethemeHandlers.push(function () {
        charts.hourlyBar.data.datasets.forEach(function (ds, i) {
            ds.backgroundColor = categoryFillColor(CATEGORY_ORDER[i]);
        });
        charts.hourlyBar.options.scales.y.grid.color = cssToken('--color-border-soft');
        Object.assign(charts.hourlyBar.options.plugins.tooltip, tooltipBaseOptions());
        charts.hourlyBar.update('none');
    });
}

function renderWeeklyLineChart(categoryStats, weeklyData) {
    const canvas = document.getElementById('weeklyLineChart');
    const emptyEl = document.getElementById('weeklyLineEmpty');
    const legendEl = document.getElementById('weeklyLineLegend');
    const isEmpty = isCategoryDataEmpty(categoryStats);
    toggleChartEmptyState(canvas, emptyEl, legendEl, isEmpty);
    if (isEmpty) return;

    const ctx = prepareChart('weeklyLineChart', 'weeklyLine');
    const days = weeklyData.map(function (day) { return day.day_korean; });
    const mobile = isMobileViewport();
    const mobileShownIndexes = [0, 2, 4, 6]; // 월·수·금·일

    const buildDatasets = function () {
        return CATEGORY_ORDER.map(function (key) {
            const cat = categoryStats.find(function (c) { return c.key === key; });
            return {
                label: cat ? cat.name : key,
                data: cat ? cat.daily_hours : days.map(function () { return 0; }),
                borderColor: categoryLineColor(key),
                backgroundColor: categoryLineColor(key),
                tension: 0,
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 4,
                borderWidth: mobile ? 2 : 2.5,
            };
        });
    };

    charts.weeklyLine = new Chart(ctx, {
        type: 'line',
        data: { labels: days, datasets: buildDatasets() },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: mobile ? {
                        autoSkip: false,
                        callback: function (val, idx) {
                            return mobileShownIndexes.includes(idx) ? days[idx] : '';
                        },
                    } : {},
                },
                y: {
                    min: 0,
                    max: 24,
                    ticks: {
                        stepSize: mobile ? 12 : 6,
                        callback: function (v) { return v + 'h'; },
                    },
                    grid: { color: cssToken('--color-border-soft') },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: Object.assign(tooltipBaseOptions(), {
                    callbacks: {
                        label: function (context) {
                            return interpolate(
                                gettext('%(label)s: %(h)sh'),
                                {label: context.dataset.label, h: context.parsed.y.toFixed(1)},
                                true
                            );
                        }
                    }
                })
            }
        }
    });

    buildCategoryLegend(legendEl, charts.weeklyLine);

    chartRethemeHandlers.push(function () {
        charts.weeklyLine.data.datasets.forEach(function (ds, i) {
            const key = CATEGORY_ORDER[i];
            ds.borderColor = categoryLineColor(key);
            ds.backgroundColor = categoryLineColor(key);
        });
        charts.weeklyLine.options.scales.y.grid.color = cssToken('--color-border-soft');
        Object.assign(charts.weeklyLine.options.plugins.tooltip, tooltipBaseOptions());
        charts.weeklyLine.update('none');
        buildCategoryLegend(legendEl, charts.weeklyLine);
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
                x: { grid: { display: false } },
                // 0–24h 고정. 기록량에 따라 눈금이 달라지면 다른 주와 눈으로
                // 비교할 수 없다 — 선 차트들과 같은 규칙이다.
                y: {
                    min: 0,
                    max: 24,
                    ticks: {
                        stepSize: isMobileViewport() ? 12 : 6,
                        callback: function (v) { return v + 'h'; },
                    },
                    grid: { color: cssToken('--color-border-soft') },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: Object.assign(tooltipBaseOptions(), {
                    callbacks: {
                        label: function (context) {
                            return interpolate(
                                gettext('%(label)s: %(h)sh'),
                                {label: context.dataset.label, h: context.parsed.y.toFixed(1)},
                                true
                            );
                        }
                    }
                })
            }
        }
    });

    chartRethemeHandlers.push(function () {
        charts.weeklyBar.data.datasets[0].backgroundColor = cssToken('--color-accent-work');
        charts.weeklyBar.options.scales.y.grid.color = cssToken('--color-border-soft');
        Object.assign(charts.weeklyBar.options.plugins.tooltip, tooltipBaseOptions());
        charts.weeklyBar.update('none');
    });
}

/** 월요일 날짜만 x축에 표시한다. start_date(그 달 1일)를 기준으로 요일을
 * 셈한다 — 응답 순서를 믿지 않는다. */
function monthWeekdays(startDateIso, dayCount) {
    const start = new Date(startDateIso + 'T00:00:00');
    return Array.from({length: dayCount}, function (_, i) {
        const d = new Date(start);
        d.setDate(start.getDate() + i);
        return d.getDay(); // 0=일 ... 1=월
    });
}

function renderMonthlyLineChart(monthlyData) {
    const canvas = document.getElementById('monthlyLineChart');
    const emptyEl = document.getElementById('monthlyLineEmpty');
    const legendEl = document.getElementById('monthlyLineLegend');
    const categoryStats = monthlyData && monthlyData.category_stats;
    const isEmpty = isCategoryDataEmpty(categoryStats);
    toggleChartEmptyState(canvas, emptyEl, legendEl, isEmpty);
    if (isEmpty) return;

    const ctx = prepareChart('monthlyLineChart', 'monthlyLine');
    const dayLabels = monthlyData.day_labels;
    const weekdays = monthlyData.start_date ? monthWeekdays(monthlyData.start_date, dayLabels.length) : [];

    const buildDatasets = function () {
        return CATEGORY_ORDER.map(function (key) {
            const cat = categoryStats.find(function (c) { return c.key === key; });
            return {
                label: cat ? cat.name : key,
                data: cat ? cat.daily_hours : dayLabels.map(function () { return 0; }),
                borderColor: categoryLineColor(key),
                backgroundColor: categoryLineColor(key),
                tension: 0,
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 4,
                borderWidth: 2,
            };
        });
    };

    charts.monthlyLine = new Chart(ctx, {
        type: 'line',
        data: { labels: dayLabels, datasets: buildDatasets() },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        autoSkip: false,
                        callback: function (val, idx) {
                            return weekdays[idx] === 1 ? dayLabels[idx] : '';
                        },
                    },
                },
                y: {
                    min: 0,
                    max: 24,
                    ticks: {
                        stepSize: 12,
                        callback: function (v) { return v + 'h'; },
                    },
                    grid: { color: cssToken('--color-border-soft') },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: Object.assign(tooltipBaseOptions(), {
                    callbacks: {
                        label: function(context) {
                            return interpolate(
                                gettext('%(label)s: %(h)sh'),
                                {label: context.dataset.label, h: context.parsed.y.toFixed(1)},
                                true
                            );
                        }
                    }
                })
            }
        }
    });

    buildCategoryLegend(legendEl, charts.monthlyLine);

    chartRethemeHandlers.push(function () {
        charts.monthlyLine.data.datasets.forEach(function (ds, i) {
            const key = CATEGORY_ORDER[i];
            ds.borderColor = categoryLineColor(key);
            ds.backgroundColor = categoryLineColor(key);
        });
        charts.monthlyLine.options.scales.y.grid.color = cssToken('--color-border-soft');
        Object.assign(charts.monthlyLine.options.plugins.tooltip, tooltipBaseOptions());
        charts.monthlyLine.update('none');
        buildCategoryLegend(legendEl, charts.monthlyLine);
    });
}


/**
 * 내려받기에는 완료 이벤트가 없다. 그래서 되돌리는 것을 시간으로 한다.
 */
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.stats-export');
    if (!form) return;

    const button = document.getElementById('statsExportBtn');
    const statusEl = document.getElementById('statsExportStatus');
    const idleLabel = button.textContent.trim();
    const busyLabel = button.dataset.busyLabel;
    let busy = false;

    form.addEventListener('submit', function (event) {
        if (busy) {
            event.preventDefault();
            return;
        }
        busy = true;
        const restoreFocus = document.activeElement === button;
        button.disabled = true;
        button.textContent = busyLabel;
        if (statusEl) statusEl.textContent = busyLabel;

        setTimeout(function () {
            busy = false;
            button.disabled = false;
            button.textContent = idleLabel;
            if (statusEl) statusEl.textContent = '';
            if (restoreFocus && document.activeElement === document.body) {
                button.focus();
            }
        }, 4000);
    });
});
