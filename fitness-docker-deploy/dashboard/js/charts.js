/**
 * Charts Module - ECharts 图表配置
 */

// 检测是否为移动端
const isMobile = window.matchMedia('(max-width: 768px)').matches;
const isSmallMobile = window.matchMedia('(max-width: 480px)').matches;

// 移动端字体大小调整
const fontSize = {
    xs: isSmallMobile ? 8 : (isMobile ? 9 : 10),
    sm: isSmallMobile ? 9 : (isMobile ? 10 : 11),
    md: isSmallMobile ? 10 : (isMobile ? 11 : 12),
    lg: isSmallMobile ? 11 : (isMobile ? 12 : 14)
};

// 全局主题配置
const chartTheme = {
    backgroundColor: 'transparent',
    textStyle: {
        color: '#9CA3AF',
        fontFamily: 'Rajdhani, Noto Sans SC, sans-serif'
    },
    title: {
        textStyle: {
            color: '#F9FAFB',
            fontSize: 14,
            fontWeight: 600
        }
    },
    legend: {
        textStyle: {
            color: '#9CA3AF'
        }
    },
    tooltip: {
        backgroundColor: '#1F2937',
        borderColor: 'rgba(0, 245, 160, 0.3)',
        borderWidth: 1,
        textStyle: {
            color: '#F9FAFB'
        }
    }
};

// 颜色配置
const colors = {
    primary: '#00F5A0',
    secondary: '#00D9FF',
    warning: '#FFB547',
    danger: '#FF5757',
    purple: '#A855F7',
    gradient: ['#00F5A0', '#00D9FF']
};

// 趋势图配置
function createTrendChart(container, data) {
    const chart = echarts.init(container);
    
    // 移动端优化：减少数据点显示
    let displayLabels = data.labels;
    let displayValues = data.values;
    
    if (isMobile && data.labels.length > 7) {
        const step = Math.ceil(data.labels.length / 7);
        displayLabels = data.labels.filter((_, i) => i % step === 0);
        displayValues = data.values.filter((_, i) => i % step === 0);
    }
    
    const option = {
        ...chartTheme,
        grid: {
            left: isMobile ? '8%' : '3%',
            right: isMobile ? '5%' : '4%',
            bottom: isMobile ? '12%' : '3%',
            top: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: displayLabels,
            axisLine: {
                lineStyle: { color: 'rgba(255,255,255,0.1)' }
            },
            axisLabel: {
                color: '#6B7280',
                fontSize: fontSize.sm,
                rotate: isMobile ? 45 : 0,
                interval: isMobile ? 'auto' : 0,
                formatter: (value) => {
                    const date = new Date(value);
                    return isMobile ? 
                        `${date.getMonth() + 1}/${date.getDate()}` :
                        `${date.getMonth() + 1}/${date.getDate()}`;
                }
            },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: {
                lineStyle: { color: 'rgba(255,255,255,0.05)' }
            },
            axisLabel: {
                color: '#6B7280',
                fontSize: fontSize.sm
            }
        },
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'axis',
            axisPointer: {
                type: isMobile ? 'line' : 'cross',
                crossStyle: {
                    color: '#999'
                }
            }
        },
        series: [{
            name: '深蹲次数',
            type: 'line',
            data: displayValues,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
                color: colors.primary,
                width: 3,
                shadowColor: 'rgba(0, 245, 160, 0.3)',
                shadowBlur: 10
            },
            itemStyle: {
                color: colors.primary,
                borderColor: '#0A0F1C',
                borderWidth: 2
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(0, 245, 160, 0.3)' },
                    { offset: 1, color: 'rgba(0, 245, 160, 0)' }
                ])
            }
        }]
    };
    
    chart.setOption(option);
    return chart;
}

// 雷达图配置
function createRadarChart(container, data) {
    const chart = echarts.init(container);
    
    const maxValues = data.dimensions.map(() => 100);
    
    const option = {
        ...chartTheme,
        radar: {
            indicator: data.dimensions.map((name, i) => ({
                name: isMobile ? name.slice(0, 2) : name,  // 移动端缩短名称
                max: maxValues[i]
            })),
            shape: 'polygon',
            splitNumber: 5,
            center: ['50%', '50%'],
            radius: isMobile ? '55%' : '65%',
            axisName: {
                color: '#9CA3AF',
                fontSize: fontSize.md,
                fontWeight: 500
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.08)'
                }
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(0, 245, 160, 0.02)', 'transparent']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.1)'
                }
            }
        },
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'item'
        },
        series: [{
            type: 'radar',
            data: [{
                value: data.values,
                name: '能力值',
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: {
                    color: colors.primary,
                    width: 2
                },
                itemStyle: {
                    color: colors.primary,
                    borderColor: '#0A0F1C',
                    borderWidth: 2
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(0, 245, 160, 0.4)' },
                        { offset: 1, color: 'rgba(0, 245, 160, 0.1)' }
                    ])
                }
            }]
        }]
    };
    
    chart.setOption(option);
    return chart;
}

// 时段分布图配置
function createTimeDistChart(container, data) {
    const chart = echarts.init(container);
    
    const option = {
        ...chartTheme,
        grid: {
            left: isMobile ? '10%' : '3%',
            right: isMobile ? '5%' : '4%',
            bottom: isMobile ? '15%' : '3%',
            top: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.labels,
            axisLine: {
                lineStyle: { color: 'rgba(255,255,255,0.1)' }
            },
            axisLabel: {
                color: '#6B7280',
                fontSize: fontSize.xs,
                interval: isMobile ? 'auto' : 3,
                rotate: isMobile ? 45 : 0
            },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: {
                lineStyle: { color: 'rgba(255,255,255,0.05)' }
            },
            axisLabel: {
                color: '#6B7280',
                fontSize: fontSize.sm
            }
        },
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        series: [{
            name: '训练次数',
            type: 'bar',
            data: data.values,
            barWidth: '60%',
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: colors.primary },
                    { offset: 1, color: 'rgba(0, 245, 160, 0.3)' }
                ]),
                borderRadius: [4, 4, 0, 0]
            },
            emphasis: {
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: colors.secondary },
                        { offset: 1, color: 'rgba(0, 217, 255, 0.3)' }
                    ])
                }
            }
        }]
    };
    
    chart.setOption(option);
    return chart;
}

// 深度分布图配置
function createDepthDistChart(container, data) {
    const chart = echarts.init(container);
    
    const option = {
        ...chartTheme,
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
        },
        legend: {
            orient: isMobile ? 'horizontal' : 'vertical',
            right: isMobile ? 'center' : '5%',
            top: isMobile ? 'bottom' : 'center',
            bottom: isMobile ? '0%' : undefined,
            textStyle: {
                color: '#9CA3AF',
                fontSize: fontSize.sm
            }
        },
        series: [{
            type: 'pie',
            radius: isMobile ? ['30%', '55%'] : ['40%', '70%'],
            center: isMobile ? ['50%', '45%'] : ['40%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 6,
                borderColor: '#0A0F1C',
                borderWidth: 3
            },
            label: {
                show: false
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: 14,
                    fontWeight: 'bold',
                    color: '#F9FAFB'
                }
            },
            labelLine: {
                show: false
            },
            data: data.labels.map((label, i) => ({
                value: data.values[i],
                name: label,
                itemStyle: {
                    color: [
                        colors.primary,
                        colors.secondary,
                        colors.warning,
                        colors.purple
                    ][i]
                }
            }))
        }]
    };
    
    chart.setOption(option);
    return chart;
}

// 详细趋势图配置
function createTrendDetailChart(container, data) {
    const chart = echarts.init(container);
    
    // 移动端优化：减少数据点
    let displayLabels = data.labels;
    let displayValues = data.values;
    
    if (isMobile && data.labels.length > 10) {
        const step = Math.ceil(data.labels.length / 10);
        displayLabels = data.labels.filter((_, i) => i % step === 0);
        displayValues = data.values.filter((_, i) => i % step === 0);
    }
    
    const option = {
        ...chartTheme,
        grid: {
            left: isMobile ? '10%' : '3%',
            right: isMobile ? '5%' : '4%',
            bottom: isMobile ? '15%' : '3%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: displayLabels,
            axisLine: {
                lineStyle: { color: 'rgba(255,255,255,0.1)' }
            },
            axisLabel: {
                color: '#6B7280',
                fontSize: fontSize.sm,
                rotate: isMobile ? 45 : 0,
                formatter: (value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                }
            },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: {
                lineStyle: { color: 'rgba(255,255,255,0.05)' }
            },
            axisLabel: {
                color: '#6B7280',
                fontSize: fontSize.sm
            }
        },
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'axis'
        },
        dataZoom: isMobile ? [{
            type: 'inside',
            start: 0,
            end: 100
        }] : [{
            type: 'inside',
            start: 0,
            end: 100
        }, {
            start: 0,
            end: 100,
            height: 20,
            bottom: 10,
            borderColor: 'rgba(255,255,255,0.1)',
            fillerColor: 'rgba(0, 245, 160, 0.2)',
            handleStyle: {
                color: colors.primary
            },
            textStyle: {
                color: '#6B7280'
            }
        }],
        series: [{
            name: data.metric === 'squats' ? '深蹲次数' : '训练时长(分钟)',
            type: 'line',
            data: displayValues,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
                color: colors.primary,
                width: 3,
                shadowColor: 'rgba(0, 245, 160, 0.3)',
                shadowBlur: 10
            },
            itemStyle: {
                color: colors.primary,
                borderColor: '#0A0F1C',
                borderWidth: 2
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(0, 245, 160, 0.4)' },
                    { offset: 1, color: 'rgba(0, 245, 160, 0)' }
                ])
            },
            markLine: {
                silent: true,
                data: [{
                    type: 'average',
                    name: '平均值'
                }],
                lineStyle: {
                    color: colors.warning,
                    type: 'dashed'
                },
                label: {
                    color: colors.warning
                }
            }
        }]
    };
    
    chart.setOption(option);
    return chart;
}

// 导出图表创建函数
window.Charts = {
    createTrendChart,
    createRadarChart,
    createTimeDistChart,
    createDepthDistChart,
    createTrendDetailChart,
    colors,
    chartTheme
};
