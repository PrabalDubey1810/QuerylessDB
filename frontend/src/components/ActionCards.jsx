import { Box, BookOpen, Video } from 'lucide-react';
import './ActionCards.css';

const cards = [
    {
        id: '3d',
        icon: Box,
        title: 'Help me to create',
        subtitle: '3D Object',
        gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #a78bfa 100%)',
        bgPattern: 'radial-gradient(circle at 80% 20%, rgba(255,255,255,0.12) 0%, transparent 50%)',
    },
    {
        id: 'comic',
        icon: BookOpen,
        title: 'Help me to create',
        subtitle: 'comic',
        gradient: 'linear-gradient(135deg, #f97316 0%, #ec4899 60%, #f472b6 100%)',
        bgPattern: 'radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%)',
    },
    {
        id: 'video',
        icon: Video,
        title: 'Help me to create',
        subtitle: 'video',
        gradient: 'linear-gradient(135deg, #06b6d4 0%, #10b981 50%, #34d399 100%)',
        bgPattern: 'radial-gradient(circle at 70% 70%, rgba(255,255,255,0.1) 0%, transparent 50%)',
    },
];

export default function ActionCards() {
    return (
        <div className="action-cards">
            {cards.map((card, i) => {
                const Icon = card.icon;
                return (
                    <button
                        key={card.id}
                        className="action-card"
                        style={{
                            '--card-gradient': card.gradient,
                            '--card-pattern': card.bgPattern,
                            animationDelay: `${0.3 + i * 0.1}s`,
                        }}
                    >
                        <div className="action-card-bg" />
                        <div className="action-card-content">
                            <p className="action-card-title">{card.title}</p>
                            <h3 className="action-card-subtitle">{card.subtitle}</h3>
                        </div>
                        <div className="action-card-icon">
                            <Icon size={32} strokeWidth={1.2} />
                        </div>
                    </button>
                );
            })}
        </div>
    );
}
