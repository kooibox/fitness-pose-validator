/**
 * Charts Module - ECharts 图表配置
 */

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
    
    const option = {
        ...chartTheme,
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
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
                fontSize: 11,
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
                fontSize: 11
            }
        },
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                crossStyle: {
                    color: '#999'
                }
            }
        },
        series: [{
            name: '深蹲次数',
            type: 'line',
            data: data.values,
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
                name: name,
                max: maxValues[i]
            })),
            shape: 'polygon',
            splitNumber: 5,
            center: ['50%', '50%'],
            radius: '65%',
            axisName: {
                color: '#9CA3AF',
                fontSize: 12,
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
            left: '3%',
            right: '4%',
            bottom: '3%',
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
                fontSize: 10,
                interval: 3
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
                fontSize: 11
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
            orient: 'vertical',
            right: '5%',
            top: 'center',
            textStyle: {
                color: '#9CA3AF',
                fontSize: 11
            }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['40%', '50%'],
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
    
    const option = {
        ...chartTheme,
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '15%',
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
                fontSize: 11,
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
                fontSize: 11
            }
        },
        tooltip: {
            ...chartTheme.tooltip,
            trigger: 'axis'
        },
        dataZoom: [{
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
            data: data.values,
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
