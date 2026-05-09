"use client";

import { useEffect, useReducer, useRef } from "react";
import { buildStreamUrl } from "./api";

// ── Types ────────────────────────────────────────────────────────────
export type RunStatus = "idle" | "running" | "complete" | "failed";
export type AgentStatus = "pending" | "running" | "complete" | "failed";

export interface AgentState {
  status: AgentStatus;
  startedAt: number | null;
  finishedAt: number | null;
  findings: Record<string, unknown>;
  citations: unknown[];
  error: string | null;
}

export interface CriticScore {
  agent: string;
  supported: string[];
  partially_supported: string[];
  unsupported: string[];
  summary: string;
}

export interface CriticResult {
  hallucination_rate: number;
  flagged_agents: string[];
  scores: CriticScore[];
}

export interface RawEvent {
  type: string;
  data: Record<string, unknown>;
  ts: number;
}

export interface RunState {
  status: RunStatus;
  company: string;
  ticker: string;
  startedAt: number | null;
  duration: number | null;
  agents: Record<string, AgentState>;
  criticResult: CriticResult | null;
  memo: string | null;
  events: RawEvent[];
  error: string | null;
}

// ── Constants ────────────────────────────────────────────────────────
const AGENT_NAMES = ["financial", "market", "people", "customer"];

function initialAgentState(): AgentState {
  return {
    status: "pending",
    startedAt: null,
    finishedAt: null,
    findings: {},
    citations: [],
    error: null,
  };
}

function initialState(company: string, ticker: string): RunState {
  return {
    status: "idle",
    company,
    ticker,
    startedAt: null,
    duration: null,
    agents: Object.fromEntries(AGENT_NAMES.map((n) => [n, initialAgentState()])),
    criticResult: null,
    memo: null,
    events: [],
    error: null,
  };
}

// ── Reducer ──────────────────────────────────────────────────────────
type Action =
  | { type: "RUN_STARTED"; ts: number }
  | { type: "AGENT_STARTED"; agent: string; ts: number }
  | { type: "AGENT_DONE"; agent: string; findings: Record<string, unknown>; citations: unknown[]; error: string | null; ts: number }
  | { type: "CRITIC_DONE"; result: CriticResult; ts: number }
  | { type: "RUN_COMPLETE"; duration: number; memo: string; ts: number }
  | { type: "RAW_EVENT"; event: RawEvent }
  | { type: "ERROR"; message: string };

function reducer(state: RunState, action: Action): RunState {
  switch (action.type) {
    case "RUN_STARTED":
      return { ...state, status: "running", startedAt: action.ts };

    case "AGENT_STARTED":
      return {
        ...state,
        agents: {
          ...state.agents,
          [action.agent]: {
            ...state.agents[action.agent],
            status: "running",
            startedAt: action.ts,
          },
        },
      };

    case "AGENT_DONE":
      return {
        ...state,
        agents: {
          ...state.agents,
          [action.agent]: {
            ...state.agents[action.agent],
            status: action.error ? "failed" : "complete",
            finishedAt: action.ts,
            findings: action.findings,
            citations: action.citations,
            error: action.error,
          },
        },
      };

    case "CRITIC_DONE":
      return { ...state, criticResult: action.result };

    case "RUN_COMPLETE":
      return { ...state, status: "complete", duration: action.duration, memo: action.memo };

    case "RAW_EVENT":
      return { ...state, events: [...state.events, action.event] };

    case "ERROR":
      return { ...state, status: "failed", error: action.message };

    default:
      return state;
  }
}

// ── Hook ─────────────────────────────────────────────────────────────
export function useRunEvents(company: string, ticker: string): RunState {
  const [state, dispatch] = useReducer(reducer, undefined, () =>
    initialState(company, ticker)
  );
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!company || !ticker) return;

    const url = buildStreamUrl(company, ticker);
    const es = new EventSource(url);
    esRef.current = es;

    function handle(eventType: string, raw: string) {
      let data: Record<string, unknown> = {};
      try { data = JSON.parse(raw); } catch { /* ignore */ }

      const ts = Date.now();
      dispatch({ type: "RAW_EVENT", event: { type: eventType, data, ts } });

      switch (eventType) {
        case "run_started":
          dispatch({ type: "RUN_STARTED", ts });
          break;

        case "agent_started":
          dispatch({ type: "AGENT_STARTED", agent: data.agent as string, ts });
          break;

        case "agent_done":
          dispatch({
            type: "AGENT_DONE",
            agent: data.agent as string,
            findings: (data.findings as Record<string, unknown>) ?? {},
            citations: (data.citations as unknown[]) ?? [],
            error: (data.error as string | null) ?? null,
            ts,
          });
          break;

        case "critic_done":
          dispatch({ type: "CRITIC_DONE", result: data as unknown as CriticResult, ts });
          break;

        case "run_complete":
          dispatch({
            type: "RUN_COMPLETE",
            duration: data.duration_s as number,
            memo: (data.memo as string) ?? "",
            ts,
          });
          es.close();
          break;
      }
    }

    // EventSource fires named events as separate listeners
    ["run_started", "agent_started", "agent_done", "critic_done", "run_complete"].forEach(
      (evt) => es.addEventListener(evt, (e) => handle(evt, (e as MessageEvent).data))
    );

    es.onerror = () => {
      dispatch({ type: "ERROR", message: "Connection lost. The run may have failed." });
      es.close();
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [company, ticker]);

  return state;
}
