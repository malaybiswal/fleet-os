"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { DEMO_STORIES } from "./demoStories";
import { MICRO_DEMO_BEATS, MICRO_DEMO_TOTAL_SECONDS } from "./microDemoBeats";

const storyByKey = new Map(DEMO_STORIES.map((story) => [story.key, story]));

export function MicroDemoScript() {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  const beat = MICRO_DEMO_BEATS[index];
  const story = beat.storyKey ? storyByKey.get(beat.storyKey) : undefined;
  const isFirst = index === 0;
  const isLast = index === MICRO_DEMO_BEATS.length - 1;

  const goNext = useCallback(() => {
    setIndex((current) => Math.min(current + 1, MICRO_DEMO_BEATS.length - 1));
  }, []);
  const goPrev = useCallback(() => {
    setIndex((current) => Math.max(current - 1, 0));
  }, []);
  const restart = useCallback(() => {
    setIndex(0);
    setPlaying(false);
  }, []);

  // Auto-advance while playing; stop when the last beat is reached.
  useEffect(() => {
    if (!playing) return;
    if (isLast) {
      setPlaying(false);
      return;
    }
    const timer = setTimeout(goNext, beat.seconds * 1000);
    return () => clearTimeout(timer);
  }, [playing, index, isLast, beat.seconds, goNext]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h1 className="text-3xl font-bold text-slate-900">60-Second Demo</h1>
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
            Demo
          </span>
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
            ~{MICRO_DEMO_TOTAL_SECONDS}s · cold outreach
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPlaying((value) => !value)}
            className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            {playing ? "Pause" : isLast ? "Replay" : "Auto-play"}
          </button>
          <button
            type="button"
            onClick={restart}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Restart
          </button>
        </div>
      </div>

      <p className="text-slate-500">
        A linear pitch for a first call — five beats, one product surface each, ending in
        the FleetOS payoff. Read each line out loud, then click through to the live screen.
      </p>

      {/* Beat progress */}
      <div className="flex items-center gap-2">
        {MICRO_DEMO_BEATS.map((item, itemIndex) => (
          <button
            key={item.id}
            type="button"
            aria-label={`Go to beat ${itemIndex + 1}: ${item.focus}`}
            onClick={() => {
              setPlaying(false);
              setIndex(itemIndex);
            }}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              itemIndex <= index ? "bg-blue-500" : "bg-slate-200"
            }`}
          />
        ))}
      </div>

      {/* Current beat */}
      <div className="rounded-xl border border-slate-200 border-l-4 border-l-blue-400 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-blue-600">
            {beat.focus}
          </span>
          <span className="text-xs font-medium text-slate-400">~{beat.seconds}s</span>
        </div>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">{beat.headline}</h2>
        <p className="mt-3 text-lg leading-relaxed text-slate-700">{beat.script}</p>

        {story && (
          <div className="mt-5 grid gap-3 rounded-lg bg-slate-50 p-4 text-sm sm:grid-cols-3">
            <Detail label="Pain" text={story.pain} />
            <Detail label="FleetOS Insight" text={story.insight} />
            <Detail label="Outcome" text={story.outcome} />
          </div>
        )}

        <div className="mt-6 border-t border-slate-100 pt-4">
          <Link
            href={beat.cta.href}
            className="inline-flex rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {beat.cta.label} →
          </Link>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={goPrev}
          disabled={isFirst}
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 enabled:hover:bg-slate-50 disabled:opacity-40"
        >
          ← Previous
        </button>
        <span className="text-sm font-medium text-slate-500">
          Beat {index + 1} of {MICRO_DEMO_BEATS.length}
        </span>
        <button
          type="button"
          onClick={goNext}
          disabled={isLast}
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 enabled:hover:bg-slate-50 disabled:opacity-40"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

function Detail({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <p className="mt-0.5 text-sm text-slate-700">{text}</p>
    </div>
  );
}
