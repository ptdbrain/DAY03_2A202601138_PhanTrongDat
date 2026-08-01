"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ChatMessage,
  defaultModels,
  estimateTokens,
  ModelConfig,
  ModelPairConfig,
  ModelState,
  StreamMetrics,
} from "@/lib/models";

type ModelKey = "economy" | "premium";

type SavedSession = {
  states: Record<ModelKey, ModelState>;
  dark: boolean;
  questions: number;
};

const STORAGE_KEY = "dual-ai-benchmark-session";

function makeInitialState(): Record<ModelKey, ModelState> {
  return {
    economy: {
      config: defaultModels.economy,
      status: "idle",
      response: "",
      memory: [],
    },
    premium: {
      config: defaultModels.premium,
      status: "idle",
      response: "",
      memory: [],
    },
  };
}

function mergeSavedStates(saved?: Partial<Record<ModelKey, ModelState>>) {
  const defaults = makeInitialState();
  if (!saved) return defaults;
  return {
    economy: {
      ...defaults.economy,
      ...saved.economy,
      config: { ...defaults.economy.config, ...saved.economy?.config },
    },
    premium: {
      ...defaults.premium,
      ...saved.premium,
      config: { ...defaults.premium.config, ...saved.premium?.config },
    },
  };
}

function applyServerConfig(
  states: Record<ModelKey, ModelState>,
  serverConfig: ModelPairConfig,
) {
  return {
    economy: {
      ...states.economy,
      config: {
        ...states.economy.config,
        modelId: serverConfig.economy.modelId,
        provider: serverConfig.economy.provider,
      },
    },
    premium: {
      ...states.premium,
      config: {
        ...states.premium.config,
        modelId: serverConfig.premium.modelId,
        provider: serverConfig.premium.provider,
      },
    },
  };
}

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function money(value?: number | null) {
  if (value == null) return "N/A";
  return `$${value.toFixed(6)}`;
}

function ms(value?: number | null) {
  if (value == null) return "N/A";
  return value < 1000 ? `${value.toFixed(0)} ms` : `${(value / 1000).toFixed(2)} s`;
}

function trimMemory(messages: ChatMessage[]) {
  return messages.slice(-20);
}

function parseSse(buffer: string) {
  const events = buffer.split("\n\n");
  return { complete: events.slice(0, -1), rest: events.at(-1) ?? "" };
}

async function runModelStream(
  key: ModelKey,
  prompt: string,
  state: ModelState,
  signal: AbortSignal,
  onToken: (key: ModelKey, token: string) => void,
  onDone: (key: ModelKey, metrics: StreamMetrics, fullText: string) => void,
  onError: (key: ModelKey, message: string) => void,
) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      config: state.config,
      memory: state.memory,
    }),
    signal,
  });

  if (!response.ok || !response.body) {
    onError(key, `Request failed: ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSse(buffer);
    buffer = parsed.rest;

    for (const raw of parsed.complete) {
      const type = raw.match(/^event: (.+)$/m)?.[1];
      const dataLine = raw.match(/^data: (.+)$/m)?.[1];
      if (!type || !dataLine) continue;
      const data = JSON.parse(dataLine);
      if (type === "token") {
        fullText += data.delta;
        onToken(key, data.delta);
      }
      if (type === "done") onDone(key, data, fullText);
      if (type === "error") onError(key, data.message ?? "Unknown error");
    }
  }
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-[var(--line)] bg-[var(--muted)] px-3 py-2">
      <div className="text-[11px] font-medium uppercase tracking-normal text-[var(--subtle)]">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  disabled,
  onChange,
}: {
  label: string;
  value: number | "";
  min: number;
  max: number;
  step: number;
  disabled: boolean;
  onChange: (value: number | "") => void;
}) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-[var(--subtle)]">{label}</span>
      <input
        className="h-10 rounded-md border border-[var(--line)] bg-[var(--bg)] px-3 text-sm disabled:opacity-50"
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(event) => {
          const next = event.target.value;
          onChange(next === "" ? "" : Number(next));
        }}
      />
    </label>
  );
}

function ConfigPanel({
  states,
  disabled,
  onChange,
}: {
  states: Record<ModelKey, ModelState>;
  disabled: boolean;
  onChange: (key: ModelKey, patch: Partial<ModelConfig>) => void;
}) {
  return (
    <section className="grid gap-4 rounded-lg border border-[var(--line)] bg-[var(--panel)] p-4 lg:grid-cols-2">
      {(["economy", "premium"] as ModelKey[]).map((key) => {
        const config = states[key].config;
        return (
          <div key={key} className="grid gap-3">
            <div>
              <h2 className="text-sm font-semibold">{config.label}</h2>
              <p className="text-xs text-[var(--subtle)]">{config.modelId}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-4">
              <NumberField
                label="Temperature"
                min={0}
                max={2}
                step={0.1}
                value={config.temperature}
                disabled={disabled}
                onChange={(value) => value !== "" && onChange(key, { temperature: value })}
              />
              <NumberField
                label="Top P"
                min={0}
                max={1}
                step={0.05}
                value={config.topP}
                disabled={disabled}
                onChange={(value) => value !== "" && onChange(key, { topP: value })}
              />
              <NumberField
                label="Top K"
                min={0}
                max={100}
                step={1}
                value={config.topK ?? ""}
                disabled={disabled}
                onChange={(value) =>
                  onChange(key, { topK: value === "" || value <= 0 ? null : value })
                }
              />
              <NumberField
                label="Max tokens"
                min={64}
                max={8192}
                step={64}
                value={config.maxTokens}
                disabled={disabled}
                onChange={(value) => value !== "" && onChange(key, { maxTokens: value })}
              />
            </div>
            <p className="text-xs text-[var(--subtle)]">
              OpenAI không hỗ trợ Top K trong Chat Completions, nên app chỉ hiển thị tham số này để so sánh cấu hình.
            </p>
          </div>
        );
      })}
    </section>
  );
}

function ModelPanel({
  modelKey,
  state,
  color,
  onClearMemory,
}: {
  modelKey: ModelKey;
  state: ModelState;
  color: string;
  onClearMemory: (key: ModelKey) => void;
}) {
  const copy = () => navigator.clipboard?.writeText(state.response);
  const metrics = state.metrics;

  return (
    <section className="flex min-h-[520px] flex-col rounded-lg border border-[var(--line)] bg-[var(--panel)]">
      <div className="flex items-start justify-between gap-3 border-b border-[var(--line)] p-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
            <h2 className="text-base font-semibold">{state.config.label}</h2>
          </div>
          <p className="mt-1 text-sm text-[var(--subtle)]">
            {state.config.provider} · {state.config.modelId}
          </p>
          <p className="mt-1 text-xs text-[var(--subtle)]">
            Temp {state.config.temperature} · Top P {state.config.topP} · Top K{" "}
            {state.config.topK ?? "off"} · Max {state.config.maxTokens}
          </p>
        </div>
        <span className="rounded-full border border-[var(--line)] px-2.5 py-1 text-xs font-medium capitalize">
          {state.status}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-b border-[var(--line)] px-4 py-3 text-sm text-[var(--subtle)]">
        <span>Memory: {Math.floor(state.memory.length / 2)}/10</span>
        <button className="rounded-md border border-[var(--line)] px-2 py-1 text-xs" onClick={() => onClearMemory(modelKey)}>
          Xóa memory
        </button>
        <button className="rounded-md border border-[var(--line)] px-2 py-1 text-xs disabled:opacity-45" disabled={!state.response} onClick={copy}>
          Sao chép
        </button>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {state.status === "idle" && !state.response ? (
          <div className="rounded-md border border-dashed border-[var(--line)] p-5 text-sm text-[var(--subtle)]">
            Nhập một câu hỏi để xem phản hồi streaming ở đây.
          </div>
        ) : (
          <div className="markdown text-sm">{state.response}</div>
        )}
        {state.error ? (
          <div className="mt-4 rounded-md border border-[var(--danger)] px-3 py-2 text-sm text-[var(--danger)]">
            {state.error}
          </div>
        ) : null}
      </div>

      <div className="border-t border-[var(--line)] p-4">
        <div className="metric-grid">
          <Metric label="TTFT" value={ms(metrics?.ttftMs)} />
          <Metric label="Latency" value={ms(metrics?.latencyMs)} />
          <Metric
            label="Speed"
            value={metrics?.tokensPerSecond ? `${metrics.tokensPerSecond.toFixed(1)} tok/s` : "N/A"}
          />
          <Metric label="Input tokens" value={metrics?.inputTokens ?? 0} />
          <Metric label="Output tokens" value={metrics?.outputTokens ?? 0} />
          <Metric label="Total cost" value={money(metrics?.totalCost)} />
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const [states, setStates] = useState<Record<ModelKey, ModelState>>(makeInitialState);
  const [prompt, setPrompt] = useState("");
  const [dark, setDark] = useState(false);
  const [questions, setQuestions] = useState(0);
  const aborters = useRef<Record<ModelKey, AbortController | null>>({
    economy: null,
    premium: null,
  });

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const saved = JSON.parse(raw) as SavedSession;
      setStates(mergeSavedStates(saved.states));
      setDark(saved.dark);
      setQuestions(saved.questions);
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((serverConfig: ModelPairConfig) => {
        setStates((current) => applyServerConfig(current, serverConfig));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ states, dark, questions }));
  }, [states, dark, questions]);

  const isRunning = states.economy.status === "streaming" || states.premium.status === "streaming";
  const promptTokens = estimateTokens(prompt);

  const totals = useMemo(() => {
    const a = states.economy.metrics;
    const b = states.premium.metrics;
    return {
      costA: a?.totalCost ?? 0,
      costB: b?.totalCost ?? 0,
      latencyA: a?.latencyMs ?? null,
      latencyB: b?.latencyMs ?? null,
    };
  }, [states]);

  function updateModel(key: ModelKey, update: Partial<ModelState>) {
    setStates((current) => ({
      ...current,
      [key]: { ...current[key], ...update },
    }));
  }

  function updateConfig(key: ModelKey, patch: Partial<ModelConfig>) {
    setStates((current) => ({
      ...current,
      [key]: {
        ...current[key],
        config: { ...current[key].config, ...patch },
      },
    }));
  }

  function clearAll() {
    aborters.current.economy?.abort();
    aborters.current.premium?.abort();
    setStates(makeInitialState());
    setQuestions(0);
    setPrompt("");
  }

  function clearMemory(key: ModelKey) {
    updateModel(key, { memory: [] });
  }

  function stopAll() {
    aborters.current.economy?.abort();
    aborters.current.premium?.abort();
    updateModel("economy", { status: "stopped" });
    updateModel("premium", { status: "stopped" });
  }

  async function submit() {
    const text = prompt.trim();
    if (!text || isRunning) return;

    setQuestions((value) => value + 1);
    setPrompt("");
    (["economy", "premium"] as ModelKey[]).forEach((key) => {
      aborters.current[key] = new AbortController();
      updateModel(key, {
        status: "streaming",
        response: "",
        error: undefined,
        metrics: undefined,
      });
    });

    const onToken = (key: ModelKey, token: string) => {
      setStates((current) => ({
        ...current,
        [key]: {
          ...current[key],
          response: current[key].response + token,
        },
      }));
    };

    const onDone = (key: ModelKey, metrics: StreamMetrics, fullText: string) => {
      setStates((current) => {
        const userMessage: ChatMessage = {
          id: uid(),
          role: "user",
          content: text,
          createdAt: Date.now(),
        };
        const assistantMessage: ChatMessage = {
          id: uid(),
          role: "assistant",
          content: fullText,
          createdAt: Date.now(),
        };
        return {
          ...current,
          [key]: {
            ...current[key],
            status: "done",
            metrics,
            config: {
              ...current[key].config,
              modelId: metrics.modelId ?? current[key].config.modelId,
            },
            memory: trimMemory([...current[key].memory, userMessage, assistantMessage]),
          },
        };
      });
    };

    const onError = (key: ModelKey, message: string) => {
      updateModel(key, { status: "error", error: message });
    };

    const tasks = (["economy", "premium"] as ModelKey[]).map((key) =>
      runModelStream(
        key,
        text,
        states[key],
        aborters.current[key]!.signal,
        onToken,
        onDone,
        onError,
      ).catch((error) => {
        if (error?.name === "AbortError") return;
        onError(key, error instanceof Error ? error.message : "Unknown error");
      }),
    );

    await Promise.allSettled(tasks);
  }

  return (
    <main className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-[var(--line)] bg-[var(--panel)]/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div>
            <h1 className="text-lg font-semibold">Dual AI Chatbot Benchmark</h1>
            <p className="text-sm text-[var(--subtle)]">
              Gửi một câu hỏi, so sánh hai model song song.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-medium">
              OpenAI API: Server
            </span>
            <button className="rounded-md border border-[var(--line)] px-3 py-2 text-sm" onClick={clearAll}>
              Cuộc trò chuyện mới
            </button>
            <button className="rounded-md border border-[var(--line)] px-3 py-2 text-sm" onClick={stopAll} disabled={!isRunning}>
              Dừng
            </button>
            <button className="rounded-md border border-[var(--line)] px-3 py-2 text-sm" onClick={() => setDark((value) => !value)}>
              {dark ? "Light" : "Dark"}
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-4 px-4 py-5">
        <ConfigPanel states={states} disabled={isRunning} onChange={updateConfig} />

        <section className="rounded-lg border border-[var(--line)] bg-[var(--panel)] p-4">
          <textarea
            className="min-h-24 w-full resize-y rounded-md border border-[var(--line)] bg-[var(--bg)] p-3 text-sm"
            placeholder="Nhập câu hỏi cho cả hai model..."
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-[var(--subtle)]">
              Ước tính: {promptTokens} token · History A {Math.floor(states.economy.memory.length / 2)}/10 · History B {Math.floor(states.premium.memory.length / 2)}/10
            </div>
            <button
              className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-45"
              disabled={!prompt.trim() || isRunning}
              onClick={submit}
            >
              Gửi đồng thời
            </button>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <ModelPanel
            modelKey="economy"
            state={states.economy}
            color="var(--economy)"
            onClearMemory={clearMemory}
          />
          <ModelPanel
            modelKey="premium"
            state={states.premium}
            color="var(--premium)"
            onClearMemory={clearMemory}
          />
        </section>

        <section className="rounded-lg border border-[var(--line)] bg-[var(--panel)] p-4">
          <h2 className="text-base font-semibold">So sánh nhanh</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-4">
            <Metric label="Số câu hỏi" value={questions} />
            <Metric label="Cost Economy" value={money(totals.costA)} />
            <Metric label="Cost Premium" value={money(totals.costB)} />
            <Metric
              label="Nhanh hơn"
              value={
                totals.latencyA == null || totals.latencyB == null
                  ? "N/A"
                  : totals.latencyA <= totals.latencyB
                    ? "Economy"
                    : "Premium"
              }
            />
          </div>
          <p className="mt-3 text-sm text-[var(--subtle)]">
            Chất lượng câu trả lời vẫn cần người dùng đánh giá thủ công; app chỉ tự so sánh tốc độ, token và chi phí.
          </p>
        </section>
      </div>
    </main>
  );
}
