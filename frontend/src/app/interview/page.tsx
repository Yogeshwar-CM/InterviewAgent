"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Mic,
    MicOff,
    Phone,
    Loader2,
    Volume2,
    ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

type Status = "idle" | "listening" | "processing" | "speaking";
type TranscriptEntry = { role: "interviewer" | "candidate"; content: string };

interface InterviewState {
    question_count: number;
    main_questions_asked: number;
    satisfaction_level: string;
    can_prompt_end: boolean;
    is_complete: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InterviewPage() {
    const router = useRouter();
    const [isConnecting, setIsConnecting] = useState(true);
    const [status, setStatus] = useState<Status>("idle");
    const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
    const [interviewState, setInterviewState] = useState<InterviewState>({
        question_count: 0,
        main_questions_asked: 0,
        satisfaction_level: "gathering_info",
        can_prompt_end: false,
        is_complete: false,
    });
    const [showEndPrompt, setShowEndPrompt] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isMuted, setIsMuted] = useState(true);

    const audioContextRef = useRef<AudioContext | null>(null);
    const activeSourceRef = useRef<AudioBufferSourceNode | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const transcriptEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [transcript]);

    useEffect(() => {
        const config = sessionStorage.getItem("interviewConfig");
        if (!config) {
            router.push("/");
            return;
        }

        const { candidateName, role, voice } = JSON.parse(config);
        initializeInterview(candidateName, role, voice);

        return () => {
            stopAudio();
            audioContextRef.current?.close();
        };
    }, [router]);

    const initializeInterview = async (candidateName: string, role: string, voice: string) => {
        try {
            setIsConnecting(true);
            setError(null);

            const response = await fetch(`${API_URL}/api/interview/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ candidate_name: candidateName, role, voice }),
            });

            if (!response.ok) throw new Error("Failed to start interview");

            const data = await response.json();
            setSessionId(data.session_id);
            sessionStorage.setItem("sessionId", data.session_id);
            setInterviewState(data.state);
            setTranscript([{ role: "interviewer", content: data.opening_message }]);

            // Dismiss loading BEFORE playing audio
            setIsConnecting(false);

            // Now play opening audio
            setStatus("speaking");
            await playAudio(data.opening_audio_base64);
            setStatus("idle");
        } catch (err) {
            console.error("Init error:", err);
            setError("Failed to connect. Make sure the server is running.");
            setIsConnecting(false);
        }
    };

    const sendAudioToServer = async (audioBlob: Blob) => {
        if (!sessionId) return;
        setStatus("processing");

        try {
            const base64 = await new Promise<string>((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve((reader.result as string).split(",")[1]);
                reader.readAsDataURL(audioBlob);
            });

            const response = await fetch(`${API_URL}/api/interview/${sessionId}/respond`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ audio: base64 }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: "Server error" }));
                throw new Error(err.detail || "Failed to process audio");
            }

            const data = await response.json();

            setTranscript((prev) => [
                ...prev,
                { role: "candidate", content: data.candidate_transcript },
                { role: "interviewer", content: data.interviewer_response },
            ]);

            setInterviewState(data.state);

            setStatus("speaking");
            await playAudio(data.audio);
            setStatus("idle");

            if (data.state.is_complete) {
                sessionStorage.setItem("interviewResult", JSON.stringify({
                    transcript: [...transcript, { role: "candidate", content: data.candidate_transcript }, { role: "interviewer", content: data.interviewer_response }],
                    state: data.state,
                }));
                router.push("/interview/complete");
            } else if (data.state.can_prompt_end && data.state.satisfaction_level === "almost_satisfied") {
                setShowEndPrompt(true);
            }
        } catch (err) {
            console.error("Respond error:", err);
            setError(err instanceof Error ? err.message : "Failed to process audio");
        }
    };

    const stopAudio = useCallback(() => {
        if (activeSourceRef.current) {
            try {
                activeSourceRef.current.stop();
                activeSourceRef.current.disconnect();
            } catch (e) { }
            activeSourceRef.current = null;
        }
    }, []);

    const playAudio = async (base64Audio: string): Promise<void> => {
        stopAudio();
        return new Promise((resolve) => {
            try {
                const binaryString = atob(base64Audio);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);

                if (!audioContextRef.current) audioContextRef.current = new AudioContext({ sampleRate: 24000 });
                const ctx = audioContextRef.current;

                const samples = new Float32Array(bytes.length / 2);
                const dataView = new DataView(bytes.buffer);
                for (let i = 0; i < samples.length; i++) samples[i] = dataView.getInt16(i * 2, true) / 32768;

                const audioBuffer = ctx.createBuffer(1, samples.length, 24000);
                audioBuffer.getChannelData(0).set(samples);

                const source = ctx.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(ctx.destination);
                source.onended = () => { activeSourceRef.current = null; resolve(); };
                activeSourceRef.current = source;
                source.start();
            } catch (e) {
                console.error("Audio playback error:", e);
                resolve();
            }
        });
    };

    const toggleMic = useCallback(async () => {
        if (isMuted) {
            stopAudio();
            if (status === "speaking") setStatus("idle");

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                streamRef.current = stream;
                const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

                audioChunksRef.current = [];
                mediaRecorder.ondataavailable = (event) => { if (event.data.size > 0) audioChunksRef.current.push(event.data); };
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                    sendAudioToServer(audioBlob);
                };

                mediaRecorder.start();
                mediaRecorderRef.current = mediaRecorder;
                setIsMuted(false);
                setStatus("listening");
            } catch (err) {
                console.error("Recording error:", err);
                setError("Microphone access denied");
            }
        } else {
            if (mediaRecorderRef.current?.state === "recording") mediaRecorderRef.current.stop();
            if (streamRef.current) { streamRef.current.getTracks().forEach((track) => track.stop()); streamRef.current = null; }
            setIsMuted(true);
        }
    }, [isMuted, status, sessionId]);

    useEffect(() => {
        if (status === "idle" && isMuted && transcript.length > 0) {
            const lastEntry = transcript[transcript.length - 1];
            if (lastEntry?.role === "interviewer") {
                const timer = setTimeout(() => toggleMic(), 500);
                return () => clearTimeout(timer);
            }
        }
    }, [status, isMuted, transcript, toggleMic]);

    const handleEndInterview = async () => {
        setShowEndPrompt(false);
        if (!sessionId) return;

        try {
            const response = await fetch(`${API_URL}/api/interview/${sessionId}/end`, { method: "POST" });
            const data = await response.json();
            sessionStorage.setItem("interviewResult", JSON.stringify({ transcript: data.transcript || transcript, state: data.state }));
            router.push("/interview/complete");
        } catch (err) {
            console.error("End interview error:", err);
        }
    };

    const getStatus = () => {
        switch (status) {
            case "listening": return { text: "Listening", color: "bg-teal-500" };
            case "processing": return { text: "Processing", color: "bg-amber-500" };
            case "speaking": return { text: "Speaking", color: "bg-blue-500" };
            default: return { text: "Ready", color: "bg-stone-400" };
        }
    };

    const statusInfo = getStatus();

    if (isConnecting) {
        return (
            <main className="min-h-screen bg-stone-50 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 text-stone-400 animate-spin mx-auto mb-4" />
                    <p className="text-stone-500 text-sm">Connecting to interviewer...</p>
                </div>
            </main>
        );
    }

    if (error) {
        return (
            <main className="min-h-screen bg-stone-50 flex items-center justify-center">
                <div className="text-center max-w-md">
                    <p className="text-red-600 mb-4">{error}</p>
                    <Button variant="outline" onClick={() => { setError(null); setStatus("idle"); }} className="border-stone-300">
                        Retry
                    </Button>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-stone-50 text-stone-900 flex flex-col">
            {/* Header */}
            <header className="border-b border-stone-200 bg-white sticky top-0 z-10">
                <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button onClick={() => router.push("/")} className="p-2 hover:bg-stone-100 rounded transition-colors">
                            <ArrowLeft className="w-5 h-5 text-stone-600" />
                        </button>
                        <div>
                            <h1 className="font-medium text-stone-800">Interview Session</h1>
                            <p className="text-sm text-stone-500">Q{interviewState.main_questions_asked} of ~5</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${statusInfo.color}`} />
                            <span className="text-sm text-stone-500">{statusInfo.text}</span>
                        </div>

                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowEndPrompt(true)}
                            disabled={!interviewState.can_prompt_end}
                            className="border-stone-300 hover:bg-stone-100 text-sm"
                        >
                            <Phone className="w-4 h-4 mr-2 rotate-[135deg]" />
                            End
                        </Button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex max-w-screen-xl mx-auto w-full">
                {/* Transcript */}
                <div className="flex-1 border-r border-stone-200 overflow-y-auto p-6 bg-white">
                    <AnimatePresence>
                        {transcript.map((entry, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mb-6"
                            >
                                <p className="text-xs text-stone-400 uppercase tracking-wider mb-2">
                                    {entry.role === "interviewer" ? "Interviewer" : "You"}
                                </p>
                                <p className={`leading-relaxed ${entry.role === "interviewer" ? "text-stone-800" : "text-stone-600"}`}>
                                    {entry.content}
                                </p>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                    <div ref={transcriptEndRef} />
                </div>

                {/* Controls Panel */}
                <div className="w-80 p-6 flex flex-col items-center justify-center space-y-6 bg-stone-50">
                    {/* Mic Button */}
                    <button
                        onClick={toggleMic}
                        disabled={status === "processing" || status === "speaking"}
                        className={`w-24 h-24 rounded-xl flex items-center justify-center transition-all shadow-sm ${!isMuted
                                ? "bg-teal-500 hover:bg-teal-600 text-white"
                                : status === "idle"
                                    ? "bg-white border border-stone-200 hover:bg-stone-50 text-stone-600"
                                    : "bg-stone-100 text-stone-400 cursor-not-allowed"
                            }`}
                    >
                        {status === "processing" ? (
                            <Loader2 className="w-8 h-8 animate-spin" />
                        ) : status === "speaking" ? (
                            <Volume2 className="w-8 h-8" />
                        ) : !isMuted ? (
                            <Mic className="w-8 h-8" />
                        ) : (
                            <MicOff className="w-8 h-8" />
                        )}
                    </button>

                    <p className="text-sm text-stone-500 text-center">
                        {status === "processing" && "Processing your response..."}
                        {status === "speaking" && "Interviewer is speaking..."}
                        {status === "listening" && "Listening... Click to send"}
                        {status === "idle" && isMuted && "Click to speak"}
                    </p>

                    {/* Progress */}
                    <div className="w-full pt-6 border-t border-stone-200">
                        <div className="flex justify-between text-xs text-stone-500 mb-2">
                            <span>Progress</span>
                            <span>{Math.round((interviewState.main_questions_asked / 5) * 100)}%</span>
                        </div>
                        <div className="h-1.5 bg-stone-200 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.min((interviewState.main_questions_asked / 5) * 100, 100)}%` }}
                                className="h-full bg-teal-500"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* End Interview Dialog */}
            <Dialog open={showEndPrompt} onOpenChange={setShowEndPrompt}>
                <DialogContent className="bg-white border-stone-200">
                    <DialogHeader>
                        <DialogTitle className="text-stone-800">End Interview?</DialogTitle>
                        <DialogDescription className="text-stone-500">
                            {interviewState.can_prompt_end
                                ? "You've covered the main questions. End now or continue?"
                                : "Are you sure you want to end early?"}
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter className="gap-2">
                        <Button variant="outline" onClick={() => setShowEndPrompt(false)} className="border-stone-300">
                            Continue
                        </Button>
                        <Button onClick={handleEndInterview} className="bg-stone-900 text-white hover:bg-stone-800">
                            End Interview
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </main>
    );
}
