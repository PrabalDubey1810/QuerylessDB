import { useState, useRef } from 'react';
import { Send, Mic, Loader2, StopCircle } from 'lucide-react';
import { transcribeAudio } from '../services/api';
import './PromptBar.css';

export default function PromptBar({ onSubmit, isLoading, dbType = 'nosql' }) {
    const [prompt, setPrompt] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!prompt.trim() || isLoading) return;
        onSubmit(prompt);
        setPrompt('');
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorderRef.current.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
                chunksRef.current = [];
                try {
                    const result = await transcribeAudio(audioBlob);
                    if (result.transcription) {
                        setPrompt(result.transcription);
                    }
                } catch (err) {
                    console.error('Transcription failed', err);
                }
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Could not access microphone.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
    };

    const dbLabel = dbType === 'sql' ? 'SQLite' : 'TinyDB';
    const dbEmoji = dbType === 'sql' ? '🗃️' : '📄';
    const dbClass = dbType === 'sql' ? 'db-pill--sql' : 'db-pill--nosql';

    return (
        <div className="prompt-bar-wrapper">
            {/* Active DB indicator pill */}
            <div className="prompt-db-bar">
                <span className={`db-pill ${dbClass}`}>
                    {dbEmoji} {dbLabel}
                </span>
                <span className="prompt-db-hint">
                    Querying <strong>{dbLabel}</strong> — change in Settings
                </span>
            </div>

            <form className="prompt-bar" onSubmit={handleSubmit}>
                <div className="prompt-input-row">
                    <input
                        className="prompt-input"
                        type="text"
                        placeholder={isRecording ? 'Listening...' : `Ask a question about your ${dbLabel} data...`}
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        disabled={isLoading || isRecording}
                    />
                </div>
                <div className="prompt-actions-row">
                    <button
                        type="button"
                        className={`prompt-action-btn ${isRecording ? 'recording' : ''}`}
                        title="Voice Input"
                        onClick={isRecording ? stopRecording : startRecording}
                    >
                        {isRecording ? <StopCircle size={20} /> : <Mic size={20} strokeWidth={1.8} />}
                    </button>

                    <button
                        type="submit"
                        className={`prompt-send-btn ${prompt.trim() ? 'active' : ''}`}
                        disabled={!prompt.trim() || isLoading}
                    >
                        {isLoading ? <Loader2 size={18} className="spin-icon" /> : <Send size={18} strokeWidth={2} />}
                    </button>
                </div>
            </form>
        </div>
    );
}
