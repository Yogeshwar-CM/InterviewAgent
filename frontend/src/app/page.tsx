"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mic, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const voices = [
  { id: "asteria", name: "Asteria", desc: "Warm & Professional" },
  { id: "luna", name: "Luna", desc: "Soft & Calm" },
  { id: "stella", name: "Stella", desc: "Clear & Confident" },
  { id: "orion", name: "Orion", desc: "Deep & Authoritative" },
  { id: "arcas", name: "Arcas", desc: "Friendly & Casual" },
  { id: "perseus", name: "Perseus", desc: "Bold & Confident" },
];

export default function Home() {
  const router = useRouter();
  const [candidateName, setCandidateName] = useState("");
  const [role, setRole] = useState("");
  const [voice, setVoice] = useState("asteria");
  const [isLoading, setIsLoading] = useState(false);

  const handleStart = async () => {
    if (!candidateName.trim() || !role.trim()) return;

    setIsLoading(true);
    sessionStorage.setItem("interviewConfig", JSON.stringify({
      candidateName: candidateName.trim(),
      role: role.trim(),
      voice,
    }));

    router.push("/interview");
  };

  return (
    <main className="min-h-screen bg-stone-50 text-stone-900 flex">
      {/* Left - Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center border-r border-stone-200 p-12 bg-white">
        <div className="max-w-md">
          <div className="w-16 h-16 rounded-lg bg-stone-100 flex items-center justify-center mb-8 border border-stone-200">
            <Mic className="w-8 h-8 text-stone-600" />
          </div>
          <h1 className="text-4xl font-light mb-4 tracking-tight text-stone-800">
            Voice Interview
          </h1>
          <p className="text-stone-500 text-lg leading-relaxed">
            AI-powered interview preparation with real-time voice interaction and comprehensive feedback.
          </p>

          <div className="mt-12 space-y-4">
            {[
              "Natural voice conversation",
              "Real-time transcription",
              "Detailed performance analysis",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3 text-sm text-stone-500">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                {feature}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right - Form */}
      <div className="flex-1 flex flex-col justify-center p-8 lg:p-12 bg-stone-50">
        <div className="max-w-md mx-auto w-full">
          <div className="lg:hidden mb-8">
            <div className="w-12 h-12 rounded-lg bg-white border border-stone-200 flex items-center justify-center mb-4">
              <Mic className="w-6 h-6 text-stone-600" />
            </div>
            <h1 className="text-2xl font-light mb-2 text-stone-800">Voice Interview</h1>
            <p className="text-sm text-stone-500">AI-powered interview preparation</p>
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-xs text-stone-500 uppercase tracking-wider">
                Your Name
              </Label>
              <Input
                id="name"
                placeholder="Enter your name"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                className="h-12 bg-white border-stone-200 text-stone-900 placeholder:text-stone-400 focus:border-teal-500 focus:ring-teal-500/20"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role" className="text-xs text-stone-500 uppercase tracking-wider">
                Position
              </Label>
              <Input
                id="role"
                placeholder="e.g., Senior Software Engineer"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="h-12 bg-white border-stone-200 text-stone-900 placeholder:text-stone-400 focus:border-teal-500 focus:ring-teal-500/20"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-xs text-stone-500 uppercase tracking-wider">
                Interviewer Voice
              </Label>
              <Select value={voice} onValueChange={setVoice}>
                <SelectTrigger className="h-12 bg-white border-stone-200 text-stone-900 focus:ring-teal-500/20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-stone-200">
                  {voices.map((v) => (
                    <SelectItem
                      key={v.id}
                      value={v.id}
                      className="text-stone-900 focus:bg-stone-100"
                    >
                      <span className="font-medium">{v.name}</span>
                      <span className="text-stone-500 ml-2 text-sm">— {v.desc}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleStart}
              disabled={!candidateName.trim() || !role.trim() || isLoading}
              className="w-full h-12 bg-stone-900 text-white hover:bg-stone-800 font-medium"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Start Interview
                  <ChevronRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </main>
  );
}
