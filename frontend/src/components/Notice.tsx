import type { ReactNode } from "react";

/** A short message: `info` for notes, `warn` for warnings and limits, `error` for failures. */
export function Notice({ kind = "info", children }: { kind?: "info" | "warn" | "error"; children: ReactNode }) {
  const tone = { info: "border-line text-muted", warn: "border-warn text-warn", error: "border-bad text-bad" }[kind];
  return (
    <p role={kind === "error" ? "alert" : "status"} className={`border-l-4 ${tone} bg-panel px-3 py-2 text-sm`}>
      {children}
    </p>
  );
}
