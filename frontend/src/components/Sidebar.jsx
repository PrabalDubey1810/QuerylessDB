import {
    Database,
    BarChart3,
    FileText,
    History,
    Search,
    Settings,
    LogOut,
    LifeBuoy,
    ShieldCheck,
} from 'lucide-react';
import './Sidebar.css';

export default function Sidebar({
    onSettingsClick,
    dbType,
    setDbType,
    currentView,
    setView,
    role,
    setRole
}) {
    const sidebarItems = [
        {
            section: 'Query', items: [
                { icon: Search, label: 'NL Query', id: 'query', active: currentView === 'chat' },
                { icon: BarChart3, label: 'Analytics', id: 'analytics', active: false },
                { icon: FileText, label: 'Reports', id: 'reports', active: false },
            ]
        },
        {
            section: 'Database', items: [
                { icon: Database, label: 'TinyDB', id: 'nosql', active: dbType === 'nosql' },
                { icon: Database, label: 'SQLite', id: 'sql', active: dbType === 'sql' },
            ]
        },
    ];
    return (
        <aside className="sidebar">
            <div className="sidebar-top">
                <div className="sidebar-logo">
                    <div className="logo-icon">
                        {/* DataSense AI icon */}
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                            <rect width="32" height="32" rx="8" fill="#6366f1" />
                            <circle cx="16" cy="16" r="5" fill="white" />
                            <path d="M16 4v6M16 22v6M4 16h6M22 16h6" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                        </svg>
                    </div>
                    <span>DataSense <strong style={{ color: '#6366f1' }}>AI</strong></span>
                </div>
            </div>

            <nav className="sidebar-nav">
                {sidebarItems.map((section, idx) => (
                    <div key={idx} className="nav-section">
                        <div className="nav-section-label">{section.section}</div>
                        {section.items.map((item) => {
                            const Icon = item.icon;
                            const isDb = section.section === 'Database';
                            const handleClick = () => {
                                if (isDb) setDbType(item.id);
                                else if (item.id === 'query') setView('chat');
                            };

                            return (
                                <button
                                    key={item.id}
                                    className={`sidebar-item ${item.active ? 'active' : ''}`}
                                    title={item.label}
                                    onClick={handleClick}
                                >
                                    <Icon size={18} className="sidebar-item-icon" />
                                    <span>{item.label}</span>
                                </button>
                            );
                        })}
                    </div>
                ))}
            </nav>

            <div className="sidebar-bottom">
                <div className="nav-section-label">Utility</div>
                <div className="role-selector sidebar-item" style={{ cursor: 'default', background: 'transparent' }}>
                    <ShieldCheck size={18} className="sidebar-item-icon" />
                    <select
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        style={{ background: 'transparent', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', outline: 'none', width: '100%' }}
                    >
                        <option value="Viewer">Viewer Role</option>
                        <option value="Admin">Admin Role</option>
                    </select>
                </div>
                <button className="sidebar-item" onClick={onSettingsClick}>
                    <Settings size={18} className="sidebar-item-icon" />
                    <span>Settings</span>
                </button>
                <button
                    className={`sidebar-item ${currentView === 'audit' ? 'active' : ''}`}
                    onClick={() => setView('audit')}
                >
                    <History size={18} className="sidebar-item-icon" />
                    <span>Audit Log</span>
                </button>
                <button className="sidebar-item">
                    <LifeBuoy size={18} className="sidebar-item-icon" />
                    <span>Help</span>
                </button>
                <button className="sidebar-item" style={{ color: '#ef4444' }}>
                    <LogOut size={18} className="sidebar-item-icon" />
                    <span>Log out</span>
                </button>
            </div>
        </aside>
    );
}
