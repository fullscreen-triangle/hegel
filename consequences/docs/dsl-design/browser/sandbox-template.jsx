import React, { useState, useRef, useCallback, useMemo, useEffect } from "react";
import {
  Files, Search, GitBranch, Play, Blocks, Settings, ChevronRight, ChevronDown,
  X, Circle, FileCode2, FileJson, FileText, Folder, FolderOpen,
  Terminal as TerminalIcon, AlertCircle, Bell, PanelBottomClose, Check,
  Eye, Code2, Trash2, RefreshCw,
} from "lucide-react";

/* ------------------------------------------------------------------ *
 *  THEME — every color VS Code uses lives here. Retheme in one place. *
 * ------------------------------------------------------------------ */
const theme = {
  titlebar: "#3c3c3c", activitybar: "#333333", activitybarFg: "#858585",
  activitybarFgActive: "#ffffff", sidebar: "#252526", sidebarFg: "#cccccc",
  sidebarHeader: "#bbbbbb", editor: "#1e1e1e", editorFg: "#d4d4d4",
  tabBar: "#252526", tabActive: "#1e1e1e", tabInactive: "#2d2d2d",
  tabFg: "#969696", tabFgActive: "#ffffff", border: "#3c3c3c",
  accent: "#0e639c", accentBright: "#007acc", statusBar: "#007acc",
  statusFg: "#ffffff", panel: "#1e1e1e", gutter: "#858585",
  lineActive: "#2a2d2e", selection: "#264f78",
};

/* ------------------------------------------------------------------ *
 *  IN-MEMORY FILE SYSTEM — swap this for real data / props.           *
 * ------------------------------------------------------------------ */
const initialFiles = {
  src: {
    type: "folder",
    children: {
      "App.jsx": {
        type: "file", lang: "jsx",
        content: `export default function App() {
  const [count, setCount] = React.useState(0);
  console.log("rendered, count =", count);
  return (
    <div className="app">
      <h1>Hello, sandbox</h1>
      <button onClick={() => setCount(count + 1)}>
        clicked {count} times
      </button>
    </div>
  );
}`,
      },
      "index.css": {
        type: "file", lang: "css",
        content: `body { margin: 0; font-family: system-ui, sans-serif;
  background: #1e1e1e; color: #d4d4d4; }
.app { display: grid; place-items: center; gap: 16px;
  min-height: 100vh; }
h1 { font-weight: 600; }
button { padding: 8px 16px; border: 0; border-radius: 6px;
  background: #007acc; color: #fff; cursor: pointer; font-size: 14px; }
button:hover { background: #0e639c; }`,
      },
      utils: {
        type: "folder",
        children: {
          "math.js": {
            type: "file", lang: "js",
            content: `export const clamp = (n, lo, hi) =>
  Math.min(Math.max(n, lo), hi);

export const lerp = (a, b, t) => a + (b - a) * t;`,
          },
        },
      },
    },
  },
  "package.json": {
    type: "file", lang: "json",
    content: `{
  "name": "sandbox",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}`,
  },
  "README.md": {
    type: "file", lang: "md",
    content: `# Sandbox

A minimal browser IDE template with a live output column.

- Edit \`src/App.jsx\` and watch the Preview update
- Console captures logs from the running app
- Compiled tab shows the assembled output`,
  },
};

/* ------------------------------------------------------------------ *
 *  COMPILE STEP — replace this with your own compiler (e.g. MPL).     *
 *  Contract: (files) -> { html, code } where html is a runnable doc  *
 *  and code is what you want shown in the "Compiled" tab.            *
 * ------------------------------------------------------------------ */
function compileProject(files) {
  const css = files?.src?.children?.["index.css"]?.content || "";
  const appSrc = files?.src?.children?.["App.jsx"]?.content || "";

  // Strip module syntax so it runs as an inline Babel script.
  const code = appSrc
    .replace(/^\s*import[^\n]*\n/gm, "")
    .replace(/export\s+default\s+/g, "");

  const consoleShim = `
    const send = (level, args) => parent.postMessage({ __sandbox: true, level,
      message: args.map(a => { try { return typeof a === "object" ? JSON.stringify(a) : String(a) }
      catch { return String(a) } }).join(" ") }, "*");
    ["log","info","warn","error"].forEach(l => { const o = console[l];
      console[l] = (...a) => { send(l, a); o.apply(console, a); }; });
    window.addEventListener("error", e => send("error", [e.message]));`;

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8" />
<style>${css}</style>
<script>${consoleShim}<\/script>
<script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"><\/script>
<script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"><\/script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"><\/script>
</head><body><div id="root"></div>
<script type="text/babel" data-presets="react">
${code}
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(React.createElement(App));
<\/script></body></html>`;

  return { html, code };
}

/* ------------------------------------------------------------------ *
 *  Helpers                                                            *
 * ------------------------------------------------------------------ */
const fileIcon = (name) => {
  if (name.endsWith(".json")) return { Icon: FileJson, color: "#cbcb41" };
  if (name.endsWith(".md")) return { Icon: FileText, color: "#519aba" };
  if (name.endsWith(".css")) return { Icon: FileCode2, color: "#42a5f5" };
  if (name.endsWith(".jsx") || name.endsWith(".js")) return { Icon: FileCode2, color: "#f0db4f" };
  return { Icon: FileText, color: "#858585" };
};
const langLabel = (lang) => ({ jsx: "JavaScript JSX", js: "JavaScript", css: "CSS", json: "JSON", md: "Markdown" }[lang] || "Plain Text");
const getNode = (tree, path) => { let n = { children: tree }; for (const p of path) { n = n.children[p]; if (!n) return null; } return n; };

/* ------------------------------------------------------------------ *
 *  File tree (recursive)                                              *
 * ------------------------------------------------------------------ */
function Tree({ tree, path = [], depth = 0, expanded, toggle, activePath, openFile }) {
  const entries = Object.entries(tree).sort((a, b) =>
    a[1].type !== b[1].type ? (a[1].type === "folder" ? -1 : 1) : a[0].localeCompare(b[0]));
  return (
    <>
      {entries.map(([name, node]) => {
        const fullPath = [...path, name];
        const key = fullPath.join("/");
        const isFolder = node.type === "folder";
        const isOpen = expanded.has(key);
        const isActive = activePath === key;
        const { Icon, color } = isFolder
          ? { Icon: isOpen ? FolderOpen : Folder, color: "#90a4ae" }
          : fileIcon(name);
        return (
          <div key={key}>
            <button
              onClick={() => (isFolder ? toggle(key) : openFile(fullPath))}
              className="flex w-full items-center gap-1 py-0.5 pr-2 text-left text-[13px] leading-relaxed transition-colors"
              style={{ paddingLeft: 8 + depth * 12, color: theme.sidebarFg, background: isActive ? theme.lineActive : "transparent" }}
              onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "#2a2d2e"; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
            >
              {isFolder ? (isOpen ? <ChevronDown size={14} className="shrink-0 opacity-70" /> : <ChevronRight size={14} className="shrink-0 opacity-70" />) : <span className="w-[14px] shrink-0" />}
              <Icon size={15} className="shrink-0" style={{ color }} />
              <span className="truncate">{name}</span>
            </button>
            {isFolder && isOpen && (
              <Tree tree={node.children} path={fullPath} depth={depth + 1} expanded={expanded} toggle={toggle} activePath={activePath} openFile={openFile} />
            )}
          </div>
        );
      })}
    </>
  );
}

/* ------------------------------------------------------------------ *
 *  Editor (line-numbered, editable). Swap the <textarea> for Monaco.  *
 * ------------------------------------------------------------------ */
function Editor({ value, onChange, onCursor }) {
  const gutterRef = useRef(null);
  const lines = value.split("\n");
  const syncScroll = (e) => { if (gutterRef.current) gutterRef.current.scrollTop = e.target.scrollTop; };
  const handleCursor = (e) => {
    const upto = e.target.value.slice(0, e.target.selectionStart);
    onCursor({ ln: upto.split("\n").length, col: upto.length - upto.lastIndexOf("\n") });
  };
  return (
    <div className="flex min-h-0 flex-1" style={{ background: theme.editor }}>
      <div ref={gutterRef} className="select-none overflow-hidden py-3 text-right font-mono text-[13px] leading-[1.5]" style={{ color: theme.gutter, minWidth: 52, paddingRight: 16 }}>
        {lines.map((_, i) => <div key={i}>{i + 1}</div>)}
      </div>
      <textarea
        value={value} onChange={(e) => onChange(e.target.value)} onScroll={syncScroll}
        onKeyUp={handleCursor} onClick={handleCursor} spellCheck={false}
        className="min-h-0 flex-1 resize-none border-0 bg-transparent py-3 pr-4 font-mono text-[13px] leading-[1.5] outline-none"
        style={{ color: theme.editorFg, tabSize: 2, caretColor: "#fff" }}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ *
 *  Output column — Preview / Console / Compiled                       *
 * ------------------------------------------------------------------ */
function OutputColumn({ srcDoc, compiled, logs, runKey, onRun, onClear }) {
  const [tab, setTab] = useState("preview");
  const tabs = [
    { id: "preview", label: "Preview", Icon: Eye },
    { id: "console", label: "Console", Icon: TerminalIcon },
    { id: "compiled", label: "Compiled", Icon: Code2 },
  ];
  const levelColor = { log: "#d4d4d4", info: "#9cdcfe", warn: "#dcdcaa", error: "#f48771" };
  return (
    <div className="flex min-w-0 flex-1 flex-col" style={{ background: theme.editor, borderLeft: `1px solid ${theme.border}` }}>
      <div className="flex h-9 shrink-0 items-center justify-between pr-2" style={{ background: theme.tabInactive }}>
        <div className="flex h-full">
          {tabs.map(({ id, label, Icon }) => {
            const active = tab === id;
            return (
              <button key={id} onClick={() => setTab(id)}
                className="relative flex items-center gap-1.5 px-3 text-[12px] transition-colors"
                style={{ color: active ? theme.tabFgActive : theme.tabFg, background: active ? theme.tabActive : "transparent" }}>
                <Icon size={13} /> {label}
                {id === "console" && logs.length > 0 && (
                  <span className="rounded-full px-1.5 text-[10px]" style={{ background: theme.accent, color: "#fff" }}>{logs.length}</span>
                )}
                {active && <span className="absolute left-0 top-0 h-0.5 w-full" style={{ background: theme.accentBright }} />}
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-1">
          {tab === "console" && (
            <button onClick={onClear} title="Clear console" className="flex h-6 w-6 items-center justify-center rounded" style={{ color: theme.tabFg }}><Trash2 size={14} /></button>
          )}
          <button onClick={onRun} title="Re-run" className="flex h-6 items-center gap-1 rounded px-2 text-[12px]" style={{ background: theme.accent, color: "#fff" }}>
            <RefreshCw size={12} /> Run
          </button>
        </div>
      </div>

      <div className="min-h-0 flex-1">
        {tab === "preview" && (
          <iframe key={runKey} title="preview" srcDoc={srcDoc} sandbox="allow-scripts"
            className="h-full w-full border-0" style={{ background: "#fff" }} />
        )}
        {tab === "console" && (
          <div className="h-full overflow-y-auto p-2 font-mono text-[12px] leading-relaxed">
            {logs.length === 0 ? (
              <div className="px-1 pt-1" style={{ color: "#5a5a5a" }}>Console output appears here.</div>
            ) : logs.map((l, i) => (
              <div key={i} className="border-b px-1 py-1" style={{ color: levelColor[l.level] || "#d4d4d4", borderColor: "#2a2a2a" }}>
                <span className="mr-2 opacity-50">{l.level}</span>{l.message}
              </div>
            ))}
          </div>
        )}
        {tab === "compiled" && (
          <pre className="h-full overflow-auto p-3 font-mono text-[12px] leading-[1.5]" style={{ color: theme.editorFg }}>{compiled}</pre>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 *  Main shell                                                         *
 * ------------------------------------------------------------------ */
export default function VSCodeSandbox() {
  const [files, setFiles] = useState(initialFiles);
  const [expanded, setExpanded] = useState(new Set(["src"]));
  const [openTabs, setOpenTabs] = useState([["src", "App.jsx"]]);
  const [activeTab, setActiveTab] = useState("src/App.jsx");
  const [dirty, setDirty] = useState(new Set());
  const [sidebar, setSidebar] = useState(true);
  const [panel, setPanel] = useState(true);
  const [activity, setActivity] = useState("files");
  const [panelTab, setPanelTab] = useState("terminal");
  const [cursor, setCursor] = useState({ ln: 1, col: 1 });

  // output / compile state
  const [srcDoc, setSrcDoc] = useState("");
  const [compiled, setCompiled] = useState("");
  const [logs, setLogs] = useState([]);
  const [runKey, setRunKey] = useState(0);

  // resizable editor|output split (percent of the split container)
  const [editorWidth, setEditorWidth] = useState(55);
  const splitRef = useRef(null);
  const dragging = useRef(false);

  const run = useCallback(() => {
    const { html, code } = compileProject(files);
    setSrcDoc(html);
    setCompiled(code);
    setLogs([]);
    setRunKey((k) => k + 1);
  }, [files]);

  // auto-run on mount + debounced on edits
  useEffect(() => {
    const t = setTimeout(run, 400);
    return () => clearTimeout(t);
  }, [files, run]);

  // capture console messages from the preview iframe
  useEffect(() => {
    const handler = (e) => {
      if (e.data && e.data.__sandbox) setLogs((l) => [...l, { level: e.data.level, message: e.data.message }]);
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  // drag handlers for the splitter
  useEffect(() => {
    const move = (e) => {
      if (!dragging.current || !splitRef.current) return;
      const r = splitRef.current.getBoundingClientRect();
      const pct = ((e.clientX - r.left) / r.width) * 100;
      setEditorWidth(Math.min(80, Math.max(25, pct)));
    };
    const up = () => { dragging.current = false; document.body.style.cursor = ""; };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
  }, []);

  const toggleFolder = useCallback((key) => {
    setExpanded((prev) => { const n = new Set(prev); n.has(key) ? n.delete(key) : n.add(key); return n; });
  }, []);
  const openFile = useCallback((pathArr) => {
    const key = pathArr.join("/");
    setOpenTabs((prev) => (prev.some((t) => t.join("/") === key) ? prev : [...prev, pathArr]));
    setActiveTab(key);
  }, []);
  const closeTab = useCallback((key, e) => {
    e.stopPropagation();
    setOpenTabs((prev) => {
      const next = prev.filter((t) => t.join("/") !== key);
      if (activeTab === key) setActiveTab(next.length ? next[next.length - 1].join("/") : null);
      return next;
    });
    setDirty((prev) => { const n = new Set(prev); n.delete(key); return n; });
  }, [activeTab]);

  const activePathArr = useMemo(() => openTabs.find((t) => t.join("/") === activeTab) || null, [openTabs, activeTab]);
  const activeNode = activePathArr ? getNode(files, activePathArr) : null;

  const updateContent = useCallback((val) => {
    if (!activePathArr) return;
    setFiles((prev) => { const next = structuredClone(prev); getNode(next, activePathArr).content = val; return next; });
    setDirty((prev) => new Set(prev).add(activeTab));
  }, [activePathArr, activeTab]);

  const activities = [
    { id: "files", Icon: Files, label: "Explorer" },
    { id: "search", Icon: Search, label: "Search" },
    { id: "git", Icon: GitBranch, label: "Source Control" },
    { id: "run", Icon: Play, label: "Run and Debug" },
    { id: "ext", Icon: Blocks, label: "Extensions" },
  ];

  return (
    <div className="flex h-[680px] w-full flex-col overflow-hidden rounded-lg text-sm shadow-2xl"
      style={{ background: theme.editor, color: theme.editorFg, border: `1px solid ${theme.border}` }}>
      {/* Title bar */}
      <div className="flex h-9 shrink-0 items-center justify-between px-3" style={{ background: theme.titlebar }}>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ background: "#ff5f56" }} />
          <span className="h-3 w-3 rounded-full" style={{ background: "#ffbd2e" }} />
          <span className="h-3 w-3 rounded-full" style={{ background: "#27c93f" }} />
        </div>
        <span className="text-xs" style={{ color: "#cccccc" }}>sandbox — Visual Studio Code</span>
        <div className="w-12" />
      </div>

      <div className="flex min-h-0 flex-1">
        {/* Activity bar */}
        <div className="flex w-12 shrink-0 flex-col items-center justify-between py-2" style={{ background: theme.activitybar }}>
          <div className="flex flex-col items-center gap-1">
            {activities.map(({ id, Icon, label }) => {
              const active = activity === id;
              return (
                <button key={id} title={label}
                  onClick={() => { if (active) setSidebar((s) => !s); else { setActivity(id); setSidebar(true); } }}
                  className="relative flex h-11 w-12 items-center justify-center transition-colors"
                  style={{ color: active ? theme.activitybarFgActive : theme.activitybarFg }}>
                  {active && <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2" style={{ background: "#ffffff" }} />}
                  <Icon size={24} strokeWidth={1.5} />
                </button>
              );
            })}
          </div>
          <button title="Settings" className="flex h-11 w-12 items-center justify-center" style={{ color: theme.activitybarFg }}>
            <Settings size={24} strokeWidth={1.5} />
          </button>
        </div>

        {/* Sidebar */}
        {sidebar && (
          <div className="flex w-60 shrink-0 flex-col overflow-hidden" style={{ background: theme.sidebar, borderRight: `1px solid ${theme.border}` }}>
            <div className="flex h-9 shrink-0 items-center px-4 text-[11px] font-medium uppercase tracking-wider" style={{ color: theme.sidebarHeader }}>
              {activities.find((a) => a.id === activity)?.label}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto pb-2">
              {activity === "files" ? (
                <Tree tree={files} expanded={expanded} toggle={toggleFolder} activePath={activeTab} openFile={openFile} />
              ) : (
                <div className="px-4 py-6 text-[13px]" style={{ color: theme.tabFg }}>{activities.find((a) => a.id === activity)?.label} panel</div>
              )}
            </div>
          </div>
        )}

        {/* Editor + Output split */}
        <div ref={splitRef} className="flex min-w-0 flex-1">
          {/* Editor column */}
          <div className="flex min-w-0 flex-col" style={{ width: `${editorWidth}%` }}>
            <div className="flex h-9 shrink-0 items-stretch overflow-x-auto" style={{ background: theme.tabInactive }}>
              {openTabs.map((pathArr) => {
                const key = pathArr.join("/");
                const name = pathArr[pathArr.length - 1];
                const active = key === activeTab;
                const isDirty = dirty.has(key);
                const { Icon, color } = fileIcon(name);
                return (
                  <div key={key} onClick={() => setActiveTab(key)}
                    className="group flex cursor-pointer items-center gap-2 border-r px-3 text-[13px]"
                    style={{ background: active ? theme.tabActive : theme.tabInactive, color: active ? theme.tabFgActive : theme.tabFg, borderColor: theme.border, borderTop: active ? `1px solid ${theme.accentBright}` : "1px solid transparent" }}>
                    <Icon size={15} style={{ color }} />
                    <span className="whitespace-nowrap">{name}</span>
                    <button onClick={(e) => closeTab(key, e)} className="flex h-5 w-5 items-center justify-center rounded" style={{ color: active ? theme.tabFgActive : theme.tabFg }}>
                      {isDirty ? <Circle size={9} fill="currentColor" className="group-hover:hidden" /> : null}
                      <X size={15} className={isDirty ? "hidden group-hover:block" : "opacity-0 group-hover:opacity-100"} />
                    </button>
                  </div>
                );
              })}
            </div>

            {activePathArr && (
              <div className="flex h-6 shrink-0 items-center gap-1 px-4 text-[12px]" style={{ background: theme.editor, color: theme.tabFg }}>
                {activePathArr.map((p, i) => (
                  <span key={i} className="flex items-center gap-1">{i > 0 && <ChevronRight size={12} className="opacity-60" />}{p}</span>
                ))}
              </div>
            )}

            {activeNode ? (
              <Editor value={activeNode.content} onChange={updateContent} onCursor={setCursor} />
            ) : (
              <div className="flex min-h-0 flex-1 items-center justify-center text-sm" style={{ background: theme.editor, color: "#5a5a5a" }}>Select a file to start editing</div>
            )}

            {panel && (
              <div className="flex h-40 shrink-0 flex-col" style={{ background: theme.panel, borderTop: `1px solid ${theme.border}` }}>
                <div className="flex h-9 items-center justify-between pr-2">
                  <div className="flex h-full items-center">
                    {[{ id: "problems", label: "Problems" }, { id: "terminal", label: "Terminal" }].map(({ id, label }) => {
                      const active = panelTab === id;
                      return (
                        <button key={id} onClick={() => setPanelTab(id)} className="relative h-full px-3 text-[11px] font-medium uppercase tracking-wider transition-colors" style={{ color: active ? theme.tabFgActive : theme.tabFg }}>
                          {label}
                          {active && <span className="absolute bottom-0 left-0 h-0.5 w-full" style={{ background: theme.accentBright }} />}
                        </button>
                      );
                    })}
                  </div>
                  <button onClick={() => setPanel(false)} style={{ color: theme.tabFg }} title="Close panel"><PanelBottomClose size={16} /></button>
                </div>
                <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-3 font-mono text-[13px] leading-relaxed">
                  {panelTab === "terminal" ? (
                    <div style={{ color: theme.editorFg }}>
                      <div><span style={{ color: "#4ec9b0" }}>sandbox</span><span style={{ color: "#569cd6" }}> ~/project</span><span style={{ color: "#ce9178" }}> $</span> npm run dev</div>
                      <div className="mt-1" style={{ color: "#6a9955" }}>VITE v5.0 ready in 312 ms</div>
                      <div style={{ color: "#9cdcfe" }}>➜ Local: http://localhost:5173/</div>
                      <div className="mt-1 flex items-center gap-2"><span style={{ color: "#ce9178" }}>$</span><span className="inline-block h-4 w-2 animate-pulse" style={{ background: "#d4d4d4" }} /></div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 pt-1" style={{ color: "#6a9955" }}><Check size={14} /> No problems have been detected in the workspace.</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Splitter */}
          <div onMouseDown={() => { dragging.current = true; document.body.style.cursor = "col-resize"; }}
            className="w-1 shrink-0 cursor-col-resize transition-colors hover:opacity-100"
            style={{ background: theme.border }} title="Drag to resize" />

          {/* Output column */}
          <OutputColumn srcDoc={srcDoc} compiled={compiled} logs={logs} runKey={runKey} onRun={run} onClear={() => setLogs([])} />
        </div>
      </div>

      {/* Status bar */}
      <div className="flex h-6 shrink-0 items-center justify-between px-3 text-[12px]" style={{ background: theme.statusBar, color: theme.statusFg }}>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-1" onClick={() => setPanel((p) => !p)}><GitBranch size={13} /> main</button>
          <span className="flex items-center gap-2">
            <span className="flex items-center gap-1"><X size={13} /> 0</span>
            <span className="flex items-center gap-1"><AlertCircle size={13} /> 0</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span>Ln {cursor.ln}, Col {cursor.col}</span>
          <span>Spaces: 2</span><span>UTF-8</span>
          <span>{activeNode ? langLabel(activeNode.lang) : "—"}</span>
          <Bell size={13} />
        </div>
      </div>
    </div>
  );
}