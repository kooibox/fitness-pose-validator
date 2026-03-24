/**
 * App Module - 应用主逻辑
 */

const state = {
    currentPage: 'overview',
    currentRange: 'today',
    currentExerciseType: null,
    charts: {},
    sessions: [],
    selectedSession: null,
    isLoading: false
};

const api = window.API;

document.addEventListener('DOMContentLoaded', () => {
    initAuth();
});

async function initAuth() {
    if (Auth.isLoggedIn()) {
        document.getElementById('loginModal').classList.add('hidden');
        showUserInfo();
        initApp();
    } else {
        document.getElementById('loginModal').classList.remove('hidden');
        initLoginForm();
    }
}

function initLoginForm() {
    const form = document.getElementById('loginForm');
    const errorEl = document.getElementById('loginError');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const btn = document.getElementById('loginBtn');
        
        btn.disabled = true;
        errorEl.style.display = 'none';
        
        try {
            await Auth.login(username, password);
            document.getElementById('loginModal').classList.add('hidden');
            showUserInfo();
            initApp();
        } catch (error) {
            errorEl.textContent = error.message;
            errorEl.style.display = 'block';
        } finally {
            btn.disabled = false;
        }
    });
}

function showUserInfo() {
    const user = Auth.getUser();
    if (user) {
        const userInfoEl = document.getElementById('userInfo');
        const avatarEl = document.getElementById('userAvatar');
        const nameEl = document.getElementById('userName');
        
        userInfoEl.style.display = 'flex';
        avatarEl.textContent = user.username ? user.username.charAt(0).toUpperCase() : 'U';
        nameEl.textContent = user.username || 'User';
        
        document.getElementById('logoutBtn').addEventListener('click', () => {
            Auth.logout();
        });
    }
}

function initApp() {
    initNavigation();
    initTimeRangeSelector();
    initExerciseSelector();
    initClock();
    loadPage(state.currentPage);
    
    window.addEventListener('resize', debounce(resizeCharts, 250));
    initMobileTouch();
}

// ============ 导航 ============
function initNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(pageName) {
    // 更新导航状态
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === pageName);
    });
    
    // 更新页面显示
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    const targetPage = document.getElementById(`${pageName}Page`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    state.currentPage = pageName;
    loadPage(pageName);
}

// ============ 时间范围选择器 ============
function initTimeRangeSelector() {
    const timeBtns = document.querySelectorAll('.time-btn');
    
    timeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            timeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentRange = btn.dataset.range;
            loadPage(state.currentPage);
        });
    });
}

function initExerciseSelector() {
    const exerciseBtns = document.querySelectorAll('.exercise-btn');
    
    exerciseBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            exerciseBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentExerciseType = btn.dataset.type === 'squat' ? null : btn.dataset.type;
            loadPage(state.currentPage);
        });
    });
}

// ============ 时钟 ============
function initClock() {
    const clockEl = document.getElementById('currentTime');
    
    function updateClock() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

// ============ 页面加载 ============
async function loadPage(pageName) {
    state.isLoading = true;
    showRefreshIndicator(true);
    
    try {
        switch (pageName) {
            case 'overview':
                await loadOverview();
                break;
            case 'trends':
                await loadTrends();
                break;
            case 'sessions':
                await loadSessions();
                break;
            case 'ability':
                await loadAbility();
                break;
        }
    } catch (error) {
        console.error(`Failed to load ${pageName}:`, error);
    } finally {
        state.isLoading = false;
        showRefreshIndicator(false);
    }
}

// ============ 概览页 ============
async function loadOverview() {
    const [overview, trend, radar, sessions] = await Promise.all([
        api.getOverview(state.currentExerciseType),
        api.getTrend('squats', '7d', state.currentExerciseType),
        api.getRadar(state.currentExerciseType),
        api.getRecentSessions(5, state.currentExerciseType)
    ]);
    
    // 更新 KPI 卡片
    if (overview) {
        updateKPICards(overview);
    }
    
    // 渲染趋势图
    if (trend) {
        const trendContainer = document.getElementById('trendChart');
        if (state.charts.trend) {
            state.charts.trend.dispose();
        }
        state.charts.trend = Charts.createTrendChart(trendContainer, trend);
    }
    
    // 渲染雷达图
    if (radar) {
        const radarContainer = document.getElementById('radarChart');
        if (state.charts.radar) {
            state.charts.radar.dispose();
        }
        state.charts.radar = Charts.createRadarChart(radarContainer, radar);
    }
    
    // 渲染最近训练表格
    if (sessions) {
        renderRecentSessions(sessions);
    }
}

function updateKPICards(data) {
    // 总训练次数
    document.getElementById('totalSessions').textContent = data.total_sessions || '--';
    document.getElementById('sessionsTrend').querySelector('span').textContent = '+12% vs上期';
    
    // 总深蹲数
    document.getElementById('totalSquats').textContent = formatNumber(data.total_squats || 0);
    document.getElementById('squatsTrend').querySelector('span').textContent = '+8% vs上期';
    
    // 平均质量分 (mock)
    document.getElementById('avgQuality').textContent = '85.2';
    document.getElementById('qualityTrend').querySelector('span').textContent = '+3% vs上期';
    
    // 本周频率
    const weeklyFreq = data.weekly_sessions || 0;
    document.getElementById('weeklyFreq').textContent = `${weeklyFreq}次`;
    
    const badge = document.getElementById('weeklyBadge');
    if (weeklyFreq >= 4) {
        badge.textContent = '达标 ✓';
        badge.classList.remove('warning');
    } else {
        badge.textContent = `差${4 - weeklyFreq}次`;
        badge.classList.add('warning');
    }
}

function renderRecentSessions(sessions) {
    const tbody = document.getElementById('recentSessionsBody');
    
    if (!sessions || sessions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">暂无训练记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = sessions.map((session, index) => {
        const startTime = new Date(session.start_time);
        const duration = session.end_time 
            ? Math.round((new Date(session.end_time) - startTime) / 1000)
            : 0;
        const qualityScore = Math.floor(Math.random() * 15) + 80; // Mock
        
        return `
            <tr class="animate-slide-in" style="animation-delay: ${index * 50}ms">
                <td>${formatDateTime(session.start_time)}</td>
                <td>
                    <span style="font-family: 'Rajdhani', sans-serif; font-weight: 600; color: var(--accent-primary)">
                        ${session.total_squats}
                    </span>
                </td>
                <td>
                    <span style="font-family: 'Rajdhani', sans-serif; font-weight: 600; color: ${qualityScore >= 85 ? 'var(--accent-primary)' : qualityScore >= 70 ? 'var(--accent-warning)' : 'var(--accent-danger)'}">
                        ${qualityScore}
                    </span>
                </td>
                <td>${formatDuration(duration)}</td>
                <td>
                    <button class="view-btn" onclick="viewSessionDetail(${session.server_session_id})">查看</button>
                </td>
            </tr>
        `;
    }).join('');
}

// ============ 趋势页 ============
async function loadTrends() {
    const period = state.currentRange === 'today' ? '7d' 
                 : state.currentRange === 'week' ? '7d'
                 : state.currentRange === 'month' ? '30d' : '90d';
    
    const [trend, timeDist, depthDist] = await Promise.all([
        api.getTrend('squats', period, state.currentExerciseType),
        api.getDistribution('time_of_day', null, state.currentExerciseType),
        api.getDistribution('depth', null, state.currentExerciseType)
    ]);
    
    // 渲染详细趋势图
    if (trend) {
        const container = document.getElementById('trendDetailChart');
        if (state.charts.trendDetail) {
            state.charts.trendDetail.dispose();
        }
        state.charts.trendDetail = Charts.createTrendDetailChart(container, trend);
    }
    
    // 渲染时段分布图
    if (timeDist) {
        const container = document.getElementById('timeDistChart');
        if (state.charts.timeDist) {
            state.charts.timeDist.dispose();
        }
        state.charts.timeDist = Charts.createTimeDistChart(container, timeDist);
    }
    
    // 渲染深度分布图
    if (depthDist) {
        const container = document.getElementById('depthDistChart');
        if (state.charts.depthDist) {
            state.charts.depthDist.dispose();
        }
        state.charts.depthDist = Charts.createDepthDistChart(container, depthDist);
    }
    
    // 更新洞察
    updateTrendInsights();
}

function updateTrendInsights() {
    const insightsEl = document.getElementById('trendInsights');
    insightsEl.innerHTML = `
        <ul>
            <li>您的训练频率从每周 2 次提升到 4 次 (+100%)</li>
            <li>平均深蹲次数从 20 次提升到 30 次 (+50%)</li>
            <li>下蹲深度持续改善，深度占比从 45% 提升到 65%</li>
            <li style="color: var(--accent-warning)">建议：周末训练频率较低，建议保持规律性</li>
        </ul>
    `;
}

// ============ 训练页 ============
async function loadSessions() {
    const sessions = await api.getRecentSessions(20, state.currentExerciseType);
    state.sessions = sessions;
    
    renderSessionsList(sessions);
}

function renderSessionsList(sessions) {
    const listEl = document.getElementById('sessionsList');
    
    if (!sessions || sessions.length === 0) {
        listEl.innerHTML = '<div class="loading-placeholder">暂无训练记录</div>';
        return;
    }
    
    listEl.innerHTML = sessions.map((session, index) => {
        const qualityScore = Math.floor(Math.random() * 15) + 80;
        const isActive = state.selectedSession === session.server_session_id;
        
        return `
            <div class="session-item ${isActive ? 'active' : ''}" 
                 onclick="selectSession(${session.server_session_id})"
                 style="animation: slideIn 0.3s ease ${index * 30}ms both">
                <div class="session-item-header">
                    <span class="session-time">${formatDateTime(session.start_time)}</span>
                    <span class="session-quality">${qualityScore}分</span>
                </div>
                <div class="session-stats">
                    <span>🏋️ ${session.total_squats}次</span>
                    <span>⏱️ ${formatDuration(Math.round((new Date(session.end_time) - new Date(session.start_time)) / 1000))}</span>
                </div>
            </div>
        `;
    }).join('');
}

function selectSession(sessionId) {
    state.selectedSession = sessionId;
    
    // 更新列表选中状态
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // 显示详情
    showSessionDetail(sessionId);
}

async function showSessionDetail(sessionId) {
    const detailCard = document.getElementById('sessionDetailCard');
    const session = state.sessions.find(s => s.server_session_id === sessionId);
    
    if (!session) return;
    
    detailCard.innerHTML = `
        <div class="session-detail-header">
            <h2>📋 训练报告</h2>
            <span class="detail-time">${formatDateTime(session.start_time)}</span>
        </div>
        
        <div class="detail-kpis">
            <div class="detail-kpi">
                <span class="detail-kpi-value">${session.total_squats}</span>
                <span class="detail-kpi-label">深蹲次数</span>
            </div>
            <div class="detail-kpi">
                <span class="detail-kpi-value">${formatDuration(Math.round((new Date(session.end_time) - new Date(session.start_time)) / 1000))}</span>
                <span class="detail-kpi-label">训练时长</span>
            </div>
            <div class="detail-kpi">
                <span class="detail-kpi-value" id="sessionScore">--</span>
                <span class="detail-kpi-label">质量评分</span>
            </div>
            <div class="detail-kpi">
                <span class="detail-kpi-value">92°</span>
                <span class="detail-kpi-label">平均深度</span>
            </div>
        </div>
        
        <div class="detail-chart">
            <h3>膝关节角度曲线</h3>
            <div id="sessionAngleChart" style="height: 250px;"></div>
        </div>
        
        <div class="detail-feedback">
            <h3>动作反馈日志</h3>
            <div class="feedback-list">
                <div class="feedback-item warning">00:15 ⚠️ 下蹲深度不足，请蹲至90度以下</div>
                <div class="feedback-item success">01:23 ✓ 动作标准，继续保持</div>
                <div class="feedback-item warning">02:45 ⚠️ 膝盖内扣，注意膝盖方向</div>
                <div class="feedback-item success">03:12 ✓ 深蹲计数 +1</div>
                <div class="feedback-item warning">05:30 ⚠️ 背部弯曲，保持挺直</div>
            </div>
        </div>
        
        <div class="analysis-section">
            <div class="analysis-header">
                <h3>🤖 AI 智能分析</h3>
                <div class="analysis-type-selector">
                    <select id="analysisType" class="analysis-select">
                        <option value="session">单次训练分析</option>
                        <option value="trend">趋势分析</option>
                        <option value="comparison">对比分析</option>
                        <option value="advice">个性化建议</option>
                        <option value="goal">目标设定</option>
                    </select>
                    <button class="analyze-btn" id="startAnalysis">
                        开始分析
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                    </button>
                </div>
            </div>
            
            <div class="analysis-result" id="analysisResult">
                <div class="analysis-loading" id="analysisLoading" style="display: none;">
                    <div class="loading-spinner"></div>
                    <span>AI 正在分析中...</span>
                </div>
                
                <div class="analysis-content" id="analysisContent" style="display: none;"></div>
            </div>
        </div>
    `;
    
    addDetailStyles();
    addAnalysisStyles();
    renderSessionAngleChart();
    
    document.getElementById('startAnalysis').addEventListener('click', async () => {
        const analysisType = document.getElementById('analysisType').value;
        await runAnalysis(sessionId, analysisType);
    });
    
    await runAnalysis(sessionId, 'session');
}

async function runAnalysis(sessionId, analysisType) {
    const loadingEl = document.getElementById('analysisLoading');
    const contentEl = document.getElementById('analysisContent');
    const scoreEl = document.getElementById('sessionScore');
    
    loadingEl.style.display = 'flex';
    contentEl.style.display = 'none';
    
    try {
        const analysis = await api.requestAnalysis([sessionId], analysisType);
        
        if (analysis) {
            renderAnalysisResult(analysis);
            
            if (analysis.score) {
                scoreEl.textContent = analysis.score.toFixed(1);
            }
        }
    } catch (error) {
        contentEl.innerHTML = `<p class="error-text">分析失败: ${error.message}</p>`;
        contentEl.style.display = 'block';
    } finally {
        loadingEl.style.display = 'none';
    }
}

function renderAnalysisResult(analysis) {
    const container = document.getElementById('analysisContent');
    
    if (!analysis) {
        container.innerHTML = '<p class="no-data">暂无分析结果</p>';
        container.style.display = 'block';
        return;
    }
    
    const isRawMode = analysis.metadata && analysis.metadata.raw_response === true;
    
    const score = analysis.score || 0;
    const scoreLevel = getScoreLevel(score);
    const scoreColor = getScoreColor(score);
    
    const insights = analysis.insights || [];
    const suggestions = analysis.suggestions || [];
    
    let insightsHtml = '';
    if (isRawMode && insights.length === 0) {
        insightsHtml = '<p class="no-data-text">详细洞察将在优化后显示</p>';
    } else {
        insightsHtml = `
            <ul class="insight-list">
                ${insights.map(insight => `
                    <li class="insight-item">
                        <span class="insight-dot"></span>
                        <span>${insight}</span>
                    </li>
                `).join('')}
            </ul>
        `;
    }
    
    let suggestionsHtml = '';
    if (isRawMode && suggestions.length === 0) {
        suggestionsHtml = '<p class="no-data-text">详细建议将在优化后显示</p>';
    } else if (suggestions.length > 0) {
        suggestionsHtml = `
            <div class="suggestion-cards">
                ${suggestions.map((suggestion, i) => `
                    <div class="suggestion-card">
                        <span class="suggestion-num">${i + 1}</span>
                        <p>${suggestion}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    const displayMetadata = analysis.metadata 
        ? Object.entries(analysis.metadata).filter(([key]) => shouldDisplayMetadata(key))
        : [];
    
    container.innerHTML = `
        <div class="analysis-score">
            <div class="score-circle" style="background: conic-gradient(${scoreColor} ${score * 3.6}deg, var(--bg-tertiary) 0deg)">
                <div class="score-inner">
                    <span class="score-value">${score.toFixed(1)}</span>
                    <span class="score-label">${scoreLevel}</span>
                </div>
            </div>
        </div>
        
        <div class="analysis-summary">
            <h4>📝 训练总结</h4>
            <p>${analysis.summary || '暂无总结'}</p>
        </div>
        
        <div class="analysis-insights">
            <h4>💡 深度洞察</h4>
            ${insightsHtml}
        </div>
        
        ${suggestionsHtml ? `
        <div class="analysis-suggestions">
            <h4>📌 改进建议</h4>
            ${suggestionsHtml}
        </div>
        ` : ''}
        
        ${displayMetadata.length > 0 ? `
        <div class="analysis-metadata">
            <h4>📊 详细评估</h4>
            <div class="metadata-grid">
                ${displayMetadata.map(([key, value]) => `
                    <div class="metadata-item">
                        <span class="metadata-label">${formatMetadataKey(key)}</span>
                        <span class="metadata-value">${formatMetadataValue(value)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        <div class="analysis-timestamp">
            分析时间: ${formatDateTime(analysis.completed_at || new Date().toISOString())}
        </div>
    `;
    
    container.style.display = 'block';
}

function getScoreLevel(score) {
    if (score >= 90) return '卓越';
    if (score >= 80) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 60) return '一般';
    return '待提升';
}

function getScoreColor(score) {
    if (score >= 80) return 'var(--accent-primary)';
    if (score >= 60) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
}

function formatMetadataKey(key) {
    const keyMap = {
        'depth_assessment': '深度评估',
        'symmetry_assessment': '对称性评估',
        'stability_assessment': '稳定性评估',
        'trend_direction': '趋势方向',
        'improvement_rate': '进步幅度',
        'current_level': '当前水平',
        'total_squats': '总深蹲数',
        'avg_depth': '平均深度',
        'symmetry_score': '对称性评分',
    };
    return keyMap[key] || key;
}

function formatMetadataValue(value) {
    if (value === null || value === undefined) {
        return '--';
    }
    if (typeof value === 'boolean') {
        return value ? '是' : '否';
    }
    if (typeof value === 'number') {
        if (value < 1 && value > -1 && value !== 0) {
            return (value * 100).toFixed(1) + '%';
        }
        return value.toFixed(1);
    }
    if (typeof value === 'string') {
        const valueMap = {
            '良好': '<span class="tag-success">良好</span>',
            '一般': '<span class="tag-warning">一般</span>',
            '需改进': '<span class="tag-danger">需改进</span>',
            '上升': '<span class="tag-success">↑ 上升</span>',
            '平稳': '<span class="tag-info">→ 平稳</span>',
            '下降': '<span class="tag-danger">↓ 下降</span>',
        };
        return valueMap[value] || value;
    }
    return String(value);
}

function shouldDisplayMetadata(key) {
    const hiddenKeys = ['raw_response', 'json_parse_error', 'error'];
    return !hiddenKeys.includes(key);
}

function addAnalysisStyles() {
    if (document.getElementById('analysisStyles')) return;
    
    const style = document.createElement('style');
    style.id = 'analysisStyles';
    style.textContent = `
        .analysis-section {
            margin-top: var(--spacing-xl);
            padding: var(--spacing-lg);
            background: var(--bg-tertiary);
            border-radius: var(--radius-lg);
            border: 1px solid rgba(0, 245, 160, 0.1);
        }
        
        .analysis-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-lg);
            flex-wrap: wrap;
            gap: var(--spacing-sm);
        }
        
        .analysis-header h3 {
            font-size: 1rem;
            color: var(--accent-primary);
        }
        
        .analysis-type-selector {
            display: flex;
            gap: var(--spacing-sm);
        }
        
        .analysis-select {
            padding: var(--spacing-sm) var(--spacing-md);
            background: var(--bg-secondary);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-size: 0.875rem;
        }
        
        .analyze-btn {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
            padding: var(--spacing-sm) var(--spacing-md);
            background: var(--gradient-primary);
            border: none;
            border-radius: var(--radius-sm);
            color: var(--bg-primary);
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all var(--transition-fast);
        }
        
        .analyze-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 10px rgba(0, 245, 160, 0.3);
        }
        
        .analyze-btn svg {
            width: 16px;
            height: 16px;
        }
        
        .analysis-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--spacing-md);
            padding: var(--spacing-xl);
            color: var(--text-muted);
        }
        
        .analysis-score {
            display: flex;
            justify-content: center;
            margin-bottom: var(--spacing-xl);
        }
        
        .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .score-inner {
            width: 100px;
            height: 100px;
            background: var(--bg-secondary);
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .score-value {
            font-family: 'Rajdhani', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-primary);
        }
        
        .score-label {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .analysis-summary,
        .analysis-insights,
        .analysis-suggestions,
        .analysis-metadata {
            margin-bottom: var(--spacing-lg);
        }
        
        .analysis-summary h4,
        .analysis-insights h4,
        .analysis-suggestions h4,
        .analysis-metadata h4 {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: var(--spacing-sm);
            color: var(--text-secondary);
        }
        
        .analysis-summary p {
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .insight-list {
            list-style: none;
            padding: 0;
        }
        
        .insight-item {
            display: flex;
            align-items: flex-start;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm) 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .insight-dot {
            width: 6px;
            height: 6px;
            background: var(--accent-primary);
            border-radius: 50%;
            margin-top: 8px;
            flex-shrink: 0;
        }
        
        .suggestion-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--spacing-sm);
        }
        
        .suggestion-card {
            display: flex;
            gap: var(--spacing-sm);
            padding: var(--spacing-md);
            background: var(--bg-secondary);
            border-radius: var(--radius-md);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .suggestion-num {
            width: 24px;
            height: 24px;
            background: var(--accent-primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--bg-primary);
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }
        
        .suggestion-card p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }
        
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: var(--spacing-sm);
        }
        
        .metadata-item {
            display: flex;
            justify-content: space-between;
            padding: var(--spacing-sm) var(--spacing-md);
            background: var(--bg-secondary);
            border-radius: var(--radius-sm);
        }
        
        .metadata-label {
            color: var(--text-muted);
            font-size: 0.75rem;
        }
        
        .metadata-value {
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .analysis-timestamp {
            text-align: right;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: var(--spacing-md);
        }
        
        .no-data-text {
            color: var(--text-muted);
            font-size: 0.875rem;
            padding: var(--spacing-md);
            text-align: center;
        }
        
        .error-text {
            color: var(--accent-danger);
            text-align: center;
            padding: var(--spacing-lg);
        }
    `;
    document.head.appendChild(style);
}

function renderSessionAngleChart() {
    const container = document.getElementById('sessionAngleChart');
    if (!container) return;
    
    // 生成模拟的角度数据
    const timeLabels = [];
    const leftAngles = [];
    const rightAngles = [];
    
    for (let i = 0; i < 100; i++) {
        timeLabels.push(i * 3);
        const baseAngle = 170 - Math.sin(i * 0.15) * 80;
        leftAngles.push(baseAngle + Math.random() * 10 - 5);
        rightAngles.push(baseAngle + Math.random() * 10 - 5);
    }
    
    const chart = echarts.init(container);
    const option = {
        ...Charts.chartTheme,
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: timeLabels.map(t => `${Math.floor(t/60)}:${(t%60).toString().padStart(2,'0')}`),
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            axisLabel: { color: '#6B7280', fontSize: 10, interval: 19 },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            min: 60,
            max: 190,
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
            axisLabel: { color: '#6B7280' }
        },
        tooltip: { ...Charts.chartTheme.tooltip, trigger: 'axis' },
        legend: {
            data: ['左膝', '右膝'],
            textStyle: { color: '#9CA3AF' },
            top: 0
        },
        series: [
            {
                name: '左膝',
                type: 'line',
                data: leftAngles,
                smooth: true,
                symbol: 'none',
                lineStyle: { color: Charts.colors.primary, width: 2 }
            },
            {
                name: '右膝',
                type: 'line',
                data: rightAngles,
                smooth: true,
                symbol: 'none',
                lineStyle: { color: Charts.colors.secondary, width: 2 }
            }
        ]
    };
    
    chart.setOption(option);
}

function addDetailStyles() {
    if (document.getElementById('detailStyles')) return;
    
    const style = document.createElement('style');
    style.id = 'detailStyles';
    style.textContent = `
        .session-detail-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-lg);
            padding-bottom: var(--spacing-md);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .session-detail-header h2 {
            font-size: 1.25rem;
            font-weight: 600;
        }
        .detail-time {
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        .detail-kpis {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-xl);
        }
        .detail-kpi {
            text-align: center;
            padding: var(--spacing-md);
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
        }
        .detail-kpi-value {
            display: block;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-primary);
        }
        .detail-kpi-label {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        .detail-chart,
        .detail-feedback,
        .detail-ai {
            margin-bottom: var(--spacing-xl);
        }
        .detail-chart h3,
        .detail-feedback h3,
        .detail-ai h3 {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: var(--spacing-md);
        }
        .feedback-list {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
        }
        .feedback-item {
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
        }
        .feedback-item.warning {
            background: rgba(255, 181, 71, 0.1);
            color: var(--accent-warning);
        }
        .feedback-item.success {
            background: rgba(0, 245, 160, 0.1);
            color: var(--accent-primary);
        }
        .detail-ai {
            padding: var(--spacing-lg);
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            border: 1px solid rgba(0, 245, 160, 0.2);
        }
        .detail-ai h3 {
            color: var(--accent-primary);
            margin-bottom: var(--spacing-md);
        }
        .ai-insights,
        .ai-suggestions {
            margin-top: var(--spacing-md);
        }
        .ai-insights h4,
        .ai-suggestions h4 {
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: var(--spacing-sm);
        }
        .detail-ai ul {
            list-style: none;
            padding-left: 0;
        }
        .detail-ai li {
            position: relative;
            padding-left: var(--spacing-lg);
            margin-bottom: var(--spacing-xs);
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        .detail-ai li::before {
            content: '•';
            position: absolute;
            left: 0;
            color: var(--accent-primary);
        }
    `;
    document.head.appendChild(style);
}

// 全局函数供 HTML 调用
window.viewSessionDetail = function(sessionId) {
    switchPage('sessions');
    setTimeout(() => {
        selectSession(sessionId);
    }, 100);
};

// ============ 能力页 ============
async function loadAbility() {
    const radar = await api.getRadar(state.currentExerciseType);
    
    // 渲染雷达图
    if (radar) {
        const container = document.getElementById('abilityRadarChart');
        if (state.charts.abilityRadar) {
            state.charts.abilityRadar.dispose();
        }
        state.charts.abilityRadar = Charts.createRadarChart(container, radar);
        
        // 更新综合评分
        const avgScore = Math.round(radar.values.reduce((a, b) => a + b, 0) / radar.values.length);
        updateScore(avgScore);
        
        // 更新维度详情
        updateDimensions(radar);
    }
    
    // 更新目标列表 (mock)
    updateGoals();
}

function updateScore(score) {
    const scoreEl = document.getElementById('overallScore');
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreLevel = document.getElementById('scoreLevel');
    const scoreStars = document.getElementById('scoreStars');
    
    // 动画显示分数
    animateValue(scoreEl, 0, score, 1000);
    
    // 更新圆环
    const circumference = 2 * Math.PI * 90;
    const offset = circumference * (1 - score / 100);
    scoreCircle.style.strokeDashoffset = offset;
    scoreCircle.style.transition = 'stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1)';
    
    // 更新等级和星级
    if (score >= 90) {
        scoreLevel.textContent = '卓越选手';
        scoreStars.textContent = '★★★★★';
    } else if (score >= 80) {
        scoreLevel.textContent = '进阶选手';
        scoreStars.textContent = '★★★★☆';
    } else if (score >= 70) {
        scoreLevel.textContent = '中级选手';
        scoreStars.textContent = '★★★☆☆';
    } else {
        scoreLevel.textContent = '初级选手';
        scoreStars.textContent = '★★☆☆☆';
    }
}

function updateDimensions(radar) {
    const listEl = document.getElementById('dimensionsList');
    const descriptions = {
        '深度': '下蹲角度稳定在 85-95°，继续保持！',
        '对称性': '左右膝盖角度差异 < 5°，平衡性良好',
        '节奏': '动作节奏一致性良好，可进一步提高稳定性',
        '稳定性': '角度波动较大，建议放慢动作节奏',
        '频率': '训练频率有待提高，建议每周 4-5 次'
    };
    
    listEl.innerHTML = radar.dimensions.map((dim, i) => `
        <div class="dimension-item">
            <div class="dimension-header">
                <span class="dimension-name">${dim}</span>
                <span class="dimension-score">${radar.values[i]}/100</span>
            </div>
            <div class="dimension-bar">
                <div class="dimension-fill" style="width: ${radar.values[i]}%"></div>
            </div>
            <div class="dimension-desc">${descriptions[dim] || '表现良好'}</div>
        </div>
    `).join('');
}

function updateGoals() {
    const listEl = document.getElementById('goalsList');
    listEl.innerHTML = `
        <div class="goal-item">
            <div class="goal-header">
                <span class="goal-name">本周目标</span>
                <span class="goal-progress">4/5 次</span>
            </div>
            <div class="goal-bar">
                <div class="goal-fill" style="width: 80%"></div>
            </div>
        </div>
        <div class="goal-item">
            <div class="goal-header">
                <span class="goal-name">本月深蹲目标</span>
                <span class="goal-progress">850/1000 次</span>
            </div>
            <div class="goal-bar">
                <div class="goal-fill" style="width: 85%"></div>
            </div>
        </div>
        <div class="goal-item">
            <div class="goal-header">
                <span class="goal-name">质量分目标</span>
                <span class="goal-progress">88/90 分</span>
            </div>
            <div class="goal-bar">
                <div class="goal-fill" style="width: 97%"></div>
            </div>
        </div>
    `;
}

// ============ 工具函数 ============
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function animateValue(el, start, end, duration) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const eased = 1 - Math.pow(1 - progress, 3);
        
        const current = Math.round(start + (end - start) * eased);
        el.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function resizeCharts() {
    Object.values(state.charts).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

function showRefreshIndicator(show) {
    const indicator = document.getElementById('refreshIndicator');
    indicator.classList.toggle('spinning', show);
}

// ============ 移动端触摸优化 ============
function initMobileTouch() {
    // 检测是否为触摸设备
    const isTouchDevice = window.matchMedia('(pointer: coarse)').matches;
    
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
        
        // 优化触摸反馈
        const touchElements = document.querySelectorAll('.nav-btn, .kpi-card, .session-card, .time-btn');
        touchElements.forEach(el => {
            el.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            }, { passive: true });
            
            el.addEventListener('touchend', function() {
                this.style.transform = '';
            }, { passive: true });
        });
        
        // 防止双击缩放
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(event) {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, { passive: false });
        
        // 优化图表触摸体验
        Object.values(state.charts).forEach(chart => {
            if (chart && chart.setOption) {
                chart.setOption({
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: {
                            type: 'line'
                        }
                    }
                });
            }
        });
    }
    
    // 监听屏幕方向变化
    window.addEventListener('orientationchange', () => {
        setTimeout(resizeCharts, 300);
    });
}

// 导出全局函数
window.switchPage = switchPage;
window.selectSession = selectSession;
