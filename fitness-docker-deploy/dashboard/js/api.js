/**
 * API Module - 服务器端 API 接口封装
 */

const API_BASE = '/api/v1';

const API = {
    async _fetch(url, options = {}) {
        const headers = {
            ...options.headers,
            ...Auth.getAuthHeaders()
        };
        
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            Auth.logout();
            throw new Error('登录已过期，请重新登录');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }
        
        return data;
    },
    
    async getOverview(exerciseType = null) {
        let url = `${API_BASE}/dashboard/overview`;
        const params = [];
        if (exerciseType) params.push(`exercise_type=${encodeURIComponent(exerciseType)}`);
        if (params.length) url += `?${params.join('&')}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : null;
    },
    
    async getTrend(metric = 'squats', period = '30d', exerciseType = null) {
        let url = `${API_BASE}/dashboard/trend?metric=${encodeURIComponent(metric)}&period=${encodeURIComponent(period)}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : null;
    },
    
    async getDistribution(metric = 'depth', exerciseType = null) {
        let url = `${API_BASE}/dashboard/distribution?metric=${encodeURIComponent(metric)}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : null;
    },
    
    async getHeatmap(period = '90d', exerciseType = null) {
        let url = `${API_BASE}/dashboard/heatmap?period=${encodeURIComponent(period)}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : null;
    },
    
    async getRadar(exerciseType = null) {
        let url = `${API_BASE}/dashboard/radar`;
        if (exerciseType) url += `?exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : null;
    },
    
    async getBestRecords(limit = 5, exerciseType = null) {
        let url = `${API_BASE}/dashboard/best-records?limit=${limit}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : [];
    },
    
    async getRecentSessions(limit = 10, exerciseType = null) {
        let url = `${API_BASE}/dashboard/recent-sessions?limit=${limit}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const data = await this._fetch(url);
        return data.status === 'success' ? data.data : [];
    },
    
    async requestAnalysis(sessionIds, analysisType = 'session', context = null) {
        const data = await this._fetch(`${API_BASE}/llm/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_ids: sessionIds,
                analysis_type: analysisType,
                context: context,
                language: 'zh'
            })
        });
        
        return data.status === 'success' ? data.data : null;
    },
    
    async getAnalysisStatus(requestId) {
        const data = await this._fetch(`${API_BASE}/llm/status/${requestId}`);
        return data.status === 'success' ? data.data : null;
    },
    
    async getAnalysisTypes() {
        const data = await this._fetch(`${API_BASE}/llm/types`);
        return data.status === 'success' ? data.data : [];
    }
};

const MockAPI = {
    async getOverview() {
        await this._delay(500);
        return {
            total_sessions: 128,
            total_squats: 3456,
            avg_squats_per_session: 27,
            avg_duration_seconds: 750,
            weekly_sessions: 4,
            monthly_sessions: 16,
            last_training_time: '2026-03-20T15:30:00'
        };
    },
    
    async getTrend(metric = 'squats', period = '30d') {
        await this._delay(300);
        const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
        const labels = [];
        const values = [];
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toISOString().split('T')[0]);
            values.push(Math.floor(Math.random() * 20) + 20);
        }
        
        return { labels, values, metric, period };
    },
    
    async getDistribution(metric = 'depth') {
        await this._delay(300);
        
        if (metric === 'depth') {
            return {
                labels: ['深度 (<90°)', '标准 (90-120°)', '浅蹲 (120-150°)', '站立 (>150°)'],
                values: [650, 250, 80, 20],
                metric
            };
        } else if (metric === 'time_of_day') {
            return {
                labels: Array.from({length: 24}, (_, i) => `${i.toString().padStart(2, '0')}:00`),
                values: [0,0,0,0,0,0,2,5,8,3,2,4,6,2,1,3,5,8,12,10,6,3,1,0],
                metric
            };
        }
        
        return { labels: [], values: [], metric };
    },
    
    async getRadar() {
        await this._delay(400);
        return {
            dimensions: ['深度', '对称性', '节奏', '稳定性', '频率'],
            values: [90, 88, 82, 78, 75]
        };
    },
    
    async getRecentSessions(limit = 10) {
        await this._delay(400);
        const sessions = [];
        
        for (let i = 0; i < limit; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            date.setHours(Math.floor(Math.random() * 12) + 8);
            date.setMinutes(Math.floor(Math.random() * 60));
            
            sessions.push({
                server_session_id: i + 1,
                client_session_id: 1000 + i,
                start_time: date.toISOString(),
                end_time: new Date(date.getTime() + (Math.floor(Math.random() * 600) + 600) * 1000).toISOString(),
                total_squats: Math.floor(Math.random() * 20) + 20,
                total_frames: Math.floor(Math.random() * 5000) + 3000,
                client_app_id: 'fitness-pose-validator'
            });
        }
        
        return sessions;
    },
    
    async requestAnalysis(sessionIds, analysisType = 'session') {
        await this._delay(1000);
        return {
            request_id: 'mock-' + Date.now(),
            status: 'completed',
            summary: '本次训练整体表现良好，深蹲动作较为标准。',
            insights: [
                '您的下蹲深度逐渐改善，继续保持',
                '左右膝盖角度对称性良好',
                '建议适当放慢动作节奏，提高稳定性'
            ],
            suggestions: [
                '尝试将下蹲深度控制在90度左右',
                '注意保持背部挺直，避免过度前倾',
                '建议每组训练后休息30-60秒'
            ],
            score: 82.5,
            metadata: {
                total_squats: 25,
                avg_depth: 95.3,
                symmetry_score: 88.0
            }
        };
    },
    
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

window.API = API;
window.MockAPI = MockAPI;