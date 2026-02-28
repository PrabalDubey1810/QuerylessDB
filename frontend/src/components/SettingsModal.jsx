import { X, Shield, FileText, Database } from 'lucide-react';
import { getAuditLogs } from '../services/api';
import { useEffect, useState } from 'react';
import './SettingsModal.css';

export default function SettingsModal({
    isOpen, onClose,
    role, setRole,
    mode, setMode,
    dbType, setDbType,
}) {
    const [activeTab, setActiveTab] = useState('settings');
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        if (activeTab === 'audit' && isOpen) {
            getAuditLogs().then(setLogs);
        }
    }, [activeTab, isOpen]);

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <div className="modal-header">
                    <h2>Application Settings</h2>
                    <button onClick={onClose} className="close-btn"><X size={20} /></button>
                </div>

                <div className="modal-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
                        onClick={() => setActiveTab('settings')}
                    >
                        <Shield size={16} /> Role &amp; Access
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
                        onClick={() => setActiveTab('audit')}
                    >
                        <FileText size={16} /> Audit Logs
                    </button>
                </div>

                <div className="modal-body">
                    {activeTab === 'settings' ? (
                        <div className="settings-section">

                            {/* ── Database selector ────────────────────── */}
                            <div className="setting-item">
                                <label>
                                    <Database size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                                    Database Engine
                                </label>
                                <div className="db-toggle-group">
                                    <button
                                        className={`db-card ${dbType === 'nosql' ? 'db-card--active' : ''}`}
                                        onClick={() => setDbType('nosql')}
                                    >
                                        <span className="db-card-icon">📄</span>
                                        <span className="db-card-name">TinyDB</span>
                                        <span className="db-card-sub">NoSQL</span>
                                    </button>
                                    <button
                                        className={`db-card ${dbType === 'sql' ? 'db-card--active' : ''}`}
                                        onClick={() => setDbType('sql')}
                                    >
                                        <span className="db-card-icon">🗃️</span>
                                        <span className="db-card-name">SQLite</span>
                                        <span className="db-card-sub">SQL</span>
                                    </button>
                                </div>
                                {dbType === 'nosql' && (
                                    <p className="db-note">📄 TinyDB — embedded file-based NoSQL. No server needed.</p>
                                )}
                            </div>

                            {/* ── Role selector ────────────────────────── */}
                            <div className="setting-item">
                                <label>User Role</label>
                                <select value={role} onChange={(e) => setRole(e.target.value)}>
                                    <option value="Viewer">Viewer (Read-Only)</option>
                                    <option value="Admin">Admin (Full Access)</option>
                                </select>
                            </div>

                            {/* ── Operation mode ───────────────────────── */}
                            <div className="setting-item">
                                <label>Operation Mode</label>
                                <div className="radio-group">
                                    <label className={`radio-option ${mode === 'query' ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="mode"
                                            value="query"
                                            checked={mode === 'query'}
                                            onChange={() => setMode('query')}
                                        />
                                        🔍 Query (Read-Only)
                                    </label>
                                    <label className={`radio-option ${mode === 'mutation' ? 'selected' : ''} ${role !== 'Admin' ? 'disabled' : ''}`}>
                                        <input
                                            type="radio"
                                            name="mode"
                                            value="mutation"
                                            checked={mode === 'mutation'}
                                            onChange={() => setMode('mutation')}
                                            disabled={role !== 'Admin'}
                                        />
                                        ✏️ Mutation (Update/Delete/Insert)
                                    </label>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="audit-section">
                            <table className="audit-table">
                                <thead>
                                    <tr>
                                        <th>Timestamp</th>
                                        <th>User</th>
                                        <th>Action</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((log, i) => (
                                        <tr key={i}>
                                            <td>{log.timestamp}</td>
                                            <td>{log.user}</td>
                                            <td>{log.action}</td>
                                            <td className={log.status.includes('Failed') ? 'status-fail' : 'status-ok'}>
                                                {log.status}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
