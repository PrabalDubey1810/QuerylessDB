import { useEffect, useState } from 'react';
import { History, Shield, RefreshCcw, MapPin, Database, User, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import './AuditLogView.css';

export default function AuditLogView() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [undoingId, setUndoingId] = useState(null);

    const fetchLogs = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/audit');
            const data = await res.json();
            setLogs(data);
        } catch (err) {
            console.error('Failed to fetch logs:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 5000); // Polling for updates
        return () => clearInterval(interval);
    }, []);

    const handleUndo = async (logId) => {
        setUndoingId(logId);
        try {
            const res = await fetch(`http://localhost:8000/api/audit/undo/${logId}`, {
                method: 'POST',
            });
            if (res.ok) {
                await fetchLogs();
            } else {
                const err = await res.json();
                alert(`Undo failed: ${err.detail}`);
            }
        } catch (err) {
            alert('Error connecting to server');
        } finally {
            setUndoingId(null);
        }
    };

    if (loading && logs.length === 0) {
        return (
            <div className="audit-view audit-loading">
                <RefreshCcw className="spin-icon" size={24} />
                <p>Loading security logs...</p>
            </div>
        );
    }

    return (
        <div className="audit-view">
            <div className="audit-header">
                <div className="header-icon">
                    <History size={20} />
                </div>
                <div>
                    <h1>Audit Log & Governance</h1>
                    <p>Track mutations and restore previous states across SQL and NoSQL databases.</p>
                </div>
            </div>

            <div className="audit-list">
                {logs.length === 0 ? (
                    <div className="audit-empty">
                        <Shield size={48} style={{ opacity: 0.1, marginBottom: 16 }} />
                        <p>No activity recorded yet.</p>
                    </div>
                ) : (
                    logs.map((log) => (
                        <div key={log.id} className={`audit-card ${log.undone ? 'is-undone' : ''}`}>
                            <div className="card-side-info">
                                <div className="action-badge">
                                    <div className={`badge-dot ${log.status === 'Success' ? 'success' : 'failed'}`} />
                                    {log.action}
                                </div>
                                <div className="log-meta">
                                    <Clock size={12} />
                                    <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                                </div>
                            </div>

                            <div className="card-main-content">
                                <div className="query-box">
                                    <code className="query-text">{log.query}</code>
                                </div>

                                <div className="log-footer">
                                    <div className="footer-item">
                                        <User size={12} />
                                        <span>{log.user}</span>
                                    </div>
                                    <div className="footer-item">
                                        <Database size={12} />
                                        <span>{log.db_type}</span>
                                    </div>
                                    {log.undone && (
                                        <div className="footer-item status-item undone">
                                            <RefreshCcw size={12} />
                                            <span>Undone</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="card-actions">
                                {log.snapshot && !log.undone && (
                                    <button
                                        className="undo-btn"
                                        onClick={() => handleUndo(log.id)}
                                        disabled={undoingId === log.id}
                                    >
                                        {undoingId === log.id ? (
                                            <RefreshCcw size={14} className="spin-icon" />
                                        ) : (
                                            <RefreshCcw size={14} />
                                        )}
                                        <span>Undo Action</span>
                                    </button>
                                )}
                                {log.undone && (
                                    <div className="reverted-badge">
                                        <CheckCircle2 size={14} />
                                        <span>Reverted</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
