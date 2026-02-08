"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    Check,
    Download,
    ArrowLeft,
    MessageSquare,
    TrendingUp,
    TrendingDown,
    ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type TranscriptEntry = { role: "interviewer" | "candidate"; content: string };

interface InterviewState {
    question_count: number;
    main_questions_asked: number;
    satisfaction_level: string;
    can_prompt_end: boolean;
    is_complete: boolean;
}

interface Analysis {
    overall_score: number;
    recommendation: "strong_hire" | "hire" | "maybe" | "no_hire";
    summary: string;
    suitability: string;
    hiring_rationale: string;
    strengths: string[];
    improvements: string[];
    skills: {
        communication: number;
        technical: number;
        problem_solving: number;
        confidence: number;
    };
    detailed_feedback: string;
}

interface InterviewResult {
    transcript: TranscriptEntry[];
    state: InterviewState;
}

export default function CompletePage() {
    const router = useRouter();
    const [result, setResult] = useState<InterviewResult | null>(null);
    const [analysis, setAnalysis] = useState<Analysis | null>(null);
    const [activeTab, setActiveTab] = useState<"overview" | "transcript">("overview");

    useEffect(() => {
        const data = sessionStorage.getItem("interviewResult");
        const sessionId = sessionStorage.getItem("sessionId");

        if (!data) {
            router.push("/");
            return;
        }

        setResult(JSON.parse(data));

        if (sessionId) {
            fetchAnalysis(sessionId);
        }
    }, [router]);

    const fetchAnalysis = async (sessionId: string) => {
        try {
            const response = await fetch(`${API_URL}/api/interview/${sessionId}/analyze`, {
                method: "POST",
            });
            if (response.ok) {
                const data = await response.json();
                setAnalysis(data.analysis);
            }
        } catch (err) {
            console.error("Analysis error:", err);
        }
    };

    const downloadTranscript = () => {
        if (!result) return;
        const text = result.transcript
            .map((entry) => `${entry.role.toUpperCase()}: ${entry.content}`)
            .join("\n\n");
        const blob = new Blob([text], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "interview_transcript.txt";
        a.click();
        URL.revokeObjectURL(url);
    };

    const getRecommendation = (rec: string) => {
        const map: Record<string, { label: string; color: string }> = {
            strong_hire: { label: "Strong Hire", color: "text-emerald-500" },
            hire: { label: "Hire", color: "text-green-500" },
            maybe: { label: "Consider", color: "text-amber-500" },
            no_hire: { label: "Pass", color: "text-red-500" },
        };
        return map[rec] || map.maybe;
    };

    if (!result) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-zinc-950">
                <div className="w-8 h-8 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin" />
            </main>
        );
    }

    const rec = analysis ? getRecommendation(analysis.recommendation) : null;

    return (
        <main className="min-h-screen bg-zinc-950 text-zinc-100">
            {/* Header */}
            <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => {
                                sessionStorage.clear();
                                router.push("/");
                            }}
                            className="p-2 hover:bg-zinc-800 rounded transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <h1 className="text-lg font-semibold">Interview Complete</h1>
                            <p className="text-sm text-zinc-500">Performance Analysis</p>
                        </div>
                    </div>
                    <Button
                        variant="outline"
                        onClick={downloadTranscript}
                        className="border-zinc-700 hover:bg-zinc-800 text-sm"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Export Transcript
                    </Button>
                </div>
            </header>

            <div className="max-w-screen-2xl mx-auto px-6 py-8">
                {/* Tab Navigation */}
                <div className="flex gap-1 mb-8 border-b border-zinc-800">
                    {[
                        { id: "overview", label: "Overview" },
                        { id: "transcript", label: "Transcript" },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as typeof activeTab)}
                            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-[2px] ${activeTab === tab.id
                                ? "border-zinc-100 text-zinc-100"
                                : "border-transparent text-zinc-500 hover:text-zinc-300"
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {activeTab === "overview" ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="grid grid-cols-12 gap-6"
                    >
                        {/* Left Column - Score & Recommendation */}
                        <div className="col-span-12 lg:col-span-3 space-y-6">
                            {/* Score Card */}
                            <div className="bg-zinc-900 border border-zinc-800 rounded p-6">
                                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-4">Overall Score</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-5xl font-light tabular-nums">
                                        {analysis?.overall_score || "—"}
                                    </span>
                                    <span className="text-zinc-500">/100</span>
                                </div>
                                {analysis && (
                                    <p className={`text-sm font-medium mt-4 ${rec?.color}`}>
                                        {rec?.label}
                                    </p>
                                )}
                            </div>

                            {/* Stats */}
                            <div className="bg-zinc-900 border border-zinc-800 rounded p-6 space-y-4">
                                <p className="text-xs text-zinc-500 uppercase tracking-wider">Statistics</p>
                                <div className="space-y-3">
                                    {[
                                        { label: "Questions Asked", value: result.state.main_questions_asked },
                                        { label: "Total Exchanges", value: result.state.question_count },
                                        { label: "Messages", value: result.transcript.length },
                                    ].map((stat) => (
                                        <div key={stat.label} className="flex justify-between items-center">
                                            <span className="text-sm text-zinc-400">{stat.label}</span>
                                            <span className="font-medium tabular-nums">{stat.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Center Column - Skills & Summary */}
                        <div className="col-span-12 lg:col-span-5 space-y-6">
                            {/* Skills */}
                            {analysis && (
                                <div className="bg-zinc-900 border border-zinc-800 rounded p-6">
                                    <p className="text-xs text-zinc-500 uppercase tracking-wider mb-6">Skill Assessment</p>
                                    <div className="space-y-5">
                                        {[
                                            { name: "Communication", value: analysis.skills.communication },
                                            { name: "Technical Knowledge", value: analysis.skills.technical },
                                            { name: "Problem Solving", value: analysis.skills.problem_solving },
                                            { name: "Confidence", value: analysis.skills.confidence },
                                        ].map((skill) => (
                                            <div key={skill.name}>
                                                <div className="flex justify-between text-sm mb-2">
                                                    <span className="text-zinc-400">{skill.name}</span>
                                                    <span className="font-medium tabular-nums">{skill.value}</span>
                                                </div>
                                                <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${skill.value}%` }}
                                                        transition={{ duration: 0.8, ease: "easeOut" }}
                                                        className="h-full bg-zinc-400"
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Suitability Assessment */}
                            {analysis && (
                                <div className="bg-zinc-900 border border-zinc-800 rounded p-6">
                                    <p className="text-xs text-zinc-500 uppercase tracking-wider mb-4">Suitability Assessment</p>
                                    <p className="text-zinc-100 leading-relaxed mb-4">{analysis.suitability}</p>
                                    <div className="pt-4 border-t border-zinc-800">
                                        <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Hiring Recommendation</p>
                                        <p className="text-zinc-400 text-sm leading-relaxed">{analysis.hiring_rationale}</p>
                                    </div>
                                </div>
                            )}

                            {/* Summary & Feedback */}
                            {analysis && (
                                <div className="bg-zinc-900 border border-zinc-800 rounded p-6">
                                    <p className="text-xs text-zinc-500 uppercase tracking-wider mb-4">Summary</p>
                                    <p className="text-zinc-300 leading-relaxed">{analysis.summary}</p>
                                    <p className="text-zinc-400 text-sm leading-relaxed mt-4">{analysis.detailed_feedback}</p>
                                </div>
                            )}
                        </div>

                        {/* Right Column - Strengths & Improvements */}
                        <div className="col-span-12 lg:col-span-4 space-y-6">
                            {/* Strengths */}
                            {analysis && (
                                <div className="bg-zinc-900 border border-zinc-800 rounded p-6">
                                    <div className="flex items-center gap-2 mb-4">
                                        <TrendingUp className="w-4 h-4 text-emerald-500" />
                                        <p className="text-xs text-zinc-500 uppercase tracking-wider">Strengths</p>
                                    </div>
                                    <ul className="space-y-3">
                                        {analysis.strengths.map((item, i) => (
                                            <li key={i} className="flex items-start gap-3 text-sm">
                                                <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                                                <span className="text-zinc-300">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Improvements */}
                            {analysis && (
                                <div className="bg-zinc-900 border border-zinc-800 rounded p-6">
                                    <div className="flex items-center gap-2 mb-4">
                                        <TrendingDown className="w-4 h-4 text-amber-500" />
                                        <p className="text-xs text-zinc-500 uppercase tracking-wider">Areas to Improve</p>
                                    </div>
                                    <ul className="space-y-3">
                                        {analysis.improvements.map((item, i) => (
                                            <li key={i} className="flex items-start gap-3 text-sm">
                                                <ChevronRight className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                                                <span className="text-zinc-300">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="max-w-3xl"
                    >
                        <div className="bg-zinc-900 border border-zinc-800 rounded divide-y divide-zinc-800">
                            {result.transcript.map((entry, index) => (
                                <div key={index} className="p-4">
                                    <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                                        {entry.role === "interviewer" ? "Interviewer" : "Candidate"}
                                    </p>
                                    <p className="text-zinc-300 leading-relaxed">{entry.content}</p>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </div>
        </main>
    );
}
