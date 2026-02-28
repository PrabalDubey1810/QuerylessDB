import { Settings } from 'lucide-react';
import './Header.css';

export default function Header({ onSettingsClick, dbType }) {
    const dbLabel = dbType === 'sql' ? 'SQLite' : 'TinyDB';
    const dbColor = dbType === 'sql' ? '#1e40af' : '#065f46';
    const dbBg = dbType === 'sql' ? '#dbeafe' : '#d1fae5';

    return (
        <header className="header">
            <div className="header-title">
                <span className="header-app-name">DataSense <span style={{ color: '#6366f1' }}>AI</span></span>
                <span className="header-db-tag" style={{ background: dbBg, color: dbColor }}>
                    {dbLabel}
                </span>
            </div>
            <div className="header-spacer" />
            <button className="header-settings-btn" onClick={onSettingsClick} title="Settings">
                <Settings size={18} strokeWidth={2} />
                <span>Settings</span>
            </button>
        </header>
    );
}
