import { Database, Code, BarChart3, AlertCircle, Loader2, Sparkles, TrendingUp, Info, Server } from 'lucide-react';
import Plot from 'react-plotly.js';
import './ResultsView.css';

export default function ResultsView({ data, loading, error }) {
    if (loading) {
        return (
            <div className="results-view results-loading">
                <Loader2 size={32} className="spin-icon" />
                <p>Analyzing data &amp; generating insights...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="results-view results-error">
                <AlertCircle size={20} />
                <p>{error}</p>
            </div>
        );
    }

    if (!data) return null;

    const renderChart = () => {
        if (!data.results || data.results.length === 0) return null;

        const keys = Object.keys(data.results[0]);
        const numericKeys = keys.filter(k => typeof data.results[0][k] === 'number');
        const categoricalKeys = keys.filter(k => typeof data.results[0][k] === 'string');

        if (numericKeys.length > 0 && categoricalKeys.length > 0) {
            return (
                <div className="unified-section chart-section">
                    <div className="section-header">
                        <BarChart3 size={16} />
                        <span>Interactive Charts</span>
                    </div>
                    <div className="chart-container">
                        <Plot
                            data={[
                                {
                                    x: data.results.map(d => d[categoricalKeys[0]]),
                                    y: data.results.map(d => d[numericKeys[0]]),
                                    type: 'bar',
                                    marker: { color: '#6366f1' },
                                },
                            ]}
                            layout={{
                                autosize: true,
                                height: 220,  /* Reduced height */
                                title: `${numericKeys[0]} by ${categoricalKeys[0]}`,
                                paper_bgcolor: 'rgba(0,0,0,0)',
                                plot_bgcolor: 'rgba(0,0,0,0)',
                                font: { color: '#64748b', size: 11 },
                                margin: { t: 30, r: 15, l: 40, b: 50 },
                            }}
                            useResizeHandler={true}
                            style={{ width: '100%' }}
                            config={{ displayModeBar: false }}
                        />
                    </div>
                </div>
            );
        }
        return null;
    };

    const renderInsightLines = (text) =>
        text.split('\n').filter(Boolean).map((line, i) => {
            const isBullet = line.trim().startsWith('-') || line.trim().startsWith('•');
            const isHeading = line.trim().startsWith('**') && line.trim().endsWith('**');
            const content = line.replace(/^\*\*(.*)\*\*$/, '$1').replace(/^[-•]\s*/, '');

            if (isHeading) return <h4 key={i} className="insight-heading">{content}</h4>;
            if (isBullet) return (
                <div key={i} className="insight-bullet">
                    <span className="bullet-dot" />
                    <span>{content}</span>
                </div>
            );
            return <p key={i} className="insight-line">{line}</p>;
        });

    return (
        <div className="results-view">
            <div className="unified-results-card">

                {/* 1. Generated Query Area */}
                {data.generated_query && (
                    <div className="unified-section query-section">
                        <div className="section-header">
                            <div className="header-icon-wrapper orange">
                                <Code size={16} />
                            </div>
                            <span className="section-title">Generated Query</span>
                        </div>
                        <div className="query-content-wrapper">
                            <pre className="result-code">{
                                data.generated_query.sql
                                    ? data.generated_query.sql.trim()
                                    : JSON.stringify(data.generated_query, null, 2)
                            }</pre>
                        </div>
                    </div>
                )}

                {/* 2. Results Table Area */}
                <div className="unified-section data-section">
                    <div className="section-header">
                        <div className="header-icon-wrapper multi">
                            <Database size={16} />
                        </div>
                        <span className="section-title">Results</span>
                        {data.count != null && (
                            <span className="record-count-label">({data.count})</span>
                        )}
                        <div className="section-actions-placeholder">
                            <TrendingUp size={14} />
                            <Search size={14} />
                            <Sparkles size={14} />
                        </div>
                    </div>

                    <div className="table-scroll-area">
                        {data.results && data.results.length > 0 ? (
                            <div className="result-table-wrapper">
                                <table className="result-table">
                                    <thead>
                                        <tr>
                                            <th></th>
                                            {Object.keys(data.results[0]).map((key) => (
                                                <th key={key}>{key}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.results.map((row, i) => (
                                            <tr key={i}>
                                                <td className="row-index">{i}</td>
                                                {Object.values(row).map((val, j) => (
                                                    <td key={j}>
                                                        {typeof val === 'object'
                                                            ? JSON.stringify(val)
                                                            : String(val)}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : data.message ? (
                            <div className="result-success-msg">
                                <Info size={16} />
                                <p>{data.message}</p>
                            </div>
                        ) : (
                            <div className="result-empty">
                                <p>No records found.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* 3. Chart Area */}
                {renderChart()}

                {/* 4. AI Analysis Area */}
                {data.insights && (
                    <div className="unified-section ai-section">
                        <div className="ai-container-inner">
                            <div className="ai-header">
                                <div className="ai-header-icon">
                                    <Sparkles size={15} />
                                </div>
                                <span className="ai-title">AI Insights</span>
                                <div className="ai-link-icon">
                                    <Code size={12} />
                                </div>
                            </div>

                            <div className="ai-scroll-area">
                                <div className="ai-content">
                                    {renderInsightLines(data.insights)}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
