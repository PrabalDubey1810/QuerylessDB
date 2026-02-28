import './WelcomeHero.css';

export default function WelcomeHero() {
    return (
        <div className="welcome-hero">
            {/* Sparkle Icon */}
            <div className="sparkle-container">
                <svg
                    className="sparkle-icon"
                    width="48"
                    height="48"
                    viewBox="0 0 48 48"
                    fill="none"
                >
                    <path
                        d="M24 4L27.5 20.5L44 24L27.5 27.5L24 44L20.5 27.5L4 24L20.5 20.5L24 4Z"
                        fill="url(#sparkleGrad)"
                    />
                    <path
                        d="M36 8L37.5 14.5L44 16L37.5 17.5L36 24L34.5 17.5L28 16L34.5 14.5L36 8Z"
                        fill="url(#sparkleGrad2)"
                        opacity="0.6"
                    />
                    <defs>
                        <linearGradient id="sparkleGrad" x1="4" y1="4" x2="44" y2="44">
                            <stop stopColor="#a5b4fc" />
                            <stop offset="0.5" stopColor="#fff" />
                            <stop offset="1" stopColor="#c4b5fd" />
                        </linearGradient>
                        <linearGradient id="sparkleGrad2" x1="28" y1="8" x2="44" y2="24">
                            <stop stopColor="#93c5fd" />
                            <stop offset="1" stopColor="#c4b5fd" />
                        </linearGradient>
                    </defs>
                </svg>
            </div>

            {/* Welcome Text */}
            <p className="welcome-subtitle">Welcome to Leonardo AI</p>
            <h1 className="welcome-title">
                How can I help?
            </h1>
        </div>
    );
}
