"use client";

import { useEffect, useState } from "react";

import { DemoStoryCard } from "@/components/demo/DemoStoryCard";
import { DEMO_STORIES } from "@/components/demo/demoStories";
import { getDemoMockLoads } from "@/lib/api";
import type { EvaluatedMockLoad } from "@/types";

export default function DemoStoriesPage() {
  const [mockLoads, setMockLoads] = useState<EvaluatedMockLoad[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDemoMockLoads()
      .then(setMockLoads)
      .catch(() => setError("Failed to load demo scenario data"))
      .finally(() => setLoading(false));
  }, []);

  const mockLoadByName = new Map(mockLoads.map((load) => [load.name, load]));

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-3xl font-bold text-slate-900">Demo Stories</h1>
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
            Demo
          </span>
        </div>
        <p className="text-slate-500">
          Scripted operational walkthroughs — each story shows the dispatcher pain, the
          FleetOS insight, and where to see the outcome live.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {loading ? (
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-400 shadow-sm">
          Loading demo scenarios…
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {DEMO_STORIES.map((story) => (
            <DemoStoryCard
              key={story.key}
              story={story}
              mockLoad={story.scenarioName ? mockLoadByName.get(story.scenarioName) : null}
            />
          ))}
        </div>
      )}
    </div>
  );
}
