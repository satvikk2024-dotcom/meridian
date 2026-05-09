"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2 } from "lucide-react";
import { createRunSlug } from "@/lib/api";

const DEMO_COMPANIES: { name: string; ticker: string }[] = [
  { name: "Apple",     ticker: "AAPL" },
  { name: "Microsoft", ticker: "MSFT" },
  { name: "Coinbase",  ticker: "COIN" },
  { name: "Tesla",     ticker: "TSLA" },
  { name: "Airbnb",    ticker: "ABNB" },
  { name: "Snowflake", ticker: "SNOW" },
];

export default function RunForm() {
  const router = useRouter();
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function doSubmit(company: string, ticker: string) {
    const trimmed = company.trim();
    if (!trimmed) {
      setError("Please enter a company name");
      return;
    }
    setError("");
    setLoading(true);
    const slug = createRunSlug(trimmed);
    const params = new URLSearchParams({ company: trimmed });
    if (ticker) params.set("ticker", ticker);
    router.push(`/runs/${slug}?${params}`);
  }

  function handleChip(name: string, ticker: string) {
    setValue(name);
    doSubmit(name, ticker);
  }

  return (
    <div className="flex flex-col gap-3 w-full" style={{ maxWidth: 600 }}>
      {/* Input + button row */}
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            if (error) setError("");
          }}
          onKeyDown={(e) => e.key === "Enter" && doSubmit(value, "")}
          placeholder="Enter a public company name..."
          disabled={loading}
          autoFocus
          className="flex-1 h-12 px-4 rounded-lg text-small font-sans
            bg-bg-surface text-fg-primary placeholder:text-fg-muted
            border border-border-default
            focus:outline-none focus:border-accent
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors duration-150"
        />
        <button
          onClick={() => doSubmit(value, "")}
          disabled={loading}
          className="h-12 px-6 rounded-lg font-mono text-small font-semibold
            bg-accent text-bg-primary
            hover:opacity-90 active:opacity-80
            disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center gap-2
            transition-opacity duration-150
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
        >
          {loading ? (
            <Loader2 size={15} className="animate-spin" />
          ) : (
            <>
              Run
              <ArrowRight size={15} />
            </>
          )}
        </button>
      </div>

      {/* Inline error */}
      {error && (
        <p className="font-mono text-small text-danger">{error}</p>
      )}

      {/* Demo company chips */}
      <div className="flex flex-wrap gap-2">
        {DEMO_COMPANIES.map(({ name, ticker }) => (
          <button
            key={name}
            onClick={() => handleChip(name, ticker)}
            disabled={loading}
            className="px-3 py-1 rounded-full font-mono text-small
              bg-bg-elevated text-fg-secondary
              border border-border-default
              hover:border-accent hover:text-fg-primary
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-colors duration-150
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  );
}
