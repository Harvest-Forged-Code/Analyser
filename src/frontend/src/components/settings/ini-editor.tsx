import { useEffect, useRef } from "react";
import { EditorView, basicSetup } from "codemirror";
import { EditorState } from "@codemirror/state";
import { StreamLanguage } from "@codemirror/language";
import { oneDark } from "@codemirror/theme-one-dark";

// Custom INI syntax tokenizer via StreamLanguage
const iniLanguage = StreamLanguage.define({
  token(stream) {
    if (stream.sol()) {
      // Comment line
      if (stream.peek() === ";" || stream.peek() === "#") {
        stream.skipToEnd();
        return "comment";
      }
      // Section header [section]
      if (stream.peek() === "[") {
        stream.skipToEnd();
        return "keyword";
      }
    }
    // Key = value
    if (stream.match(/^[^=\n]+(?==)/)) {
      return "variableName";
    }
    if (stream.eat("=")) {
      return "operator";
    }
    stream.skipToEnd();
    return "string";
  },
});

interface IniEditorProps {
  value: string;
  onChange: (value: string) => void;
  isDark: boolean;
}

export default function IniEditor({ value, onChange, isDark }: IniEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!containerRef.current) return;

    const extensions = [
      basicSetup,
      iniLanguage,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          onChangeRef.current(update.state.doc.toString());
        }
      }),
      EditorView.theme({
        "&": { height: "420px", fontSize: "13px" },
        ".cm-scroller": { overflow: "auto", fontFamily: "monospace" },
      }),
    ];

    if (isDark) {
      extensions.push(oneDark);
    }

    const state = EditorState.create({
      doc: value,
      extensions,
    });

    const view = new EditorView({ state, parent: containerRef.current });
    viewRef.current = view;

    return () => {
      view.destroy();
      viewRef.current = null;
    };
    // Only recreate editor when dark mode changes (not on every value change)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDark]);

  // Sync external value changes (e.g. reset) without recreating the editor
  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    const current = view.state.doc.toString();
    if (current !== value) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: value },
      });
    }
  }, [value]);

  return (
    <div
      ref={containerRef}
      className="w-full overflow-hidden rounded-md border border-input"
    />
  );
}
