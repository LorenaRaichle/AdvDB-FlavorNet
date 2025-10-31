import { useState } from "react";

interface TagInputProps {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}

export default function TagInput({
  label,
  values,
  onChange,
  placeholder = "Type and press Enter",
}: TagInputProps) {
  const [draft, setDraft] = useState("");

  const addTag = (value: string) => {
    const normalized = value.trim();
    if (!normalized) return;
    if (values.some((item) => item.toLowerCase() === normalized.toLowerCase()))
      return;
    onChange([...values, normalized]);
    setDraft("");
  };

  const removeTag = (index: number) => {
    onChange(values.filter((_, idx) => idx !== index));
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addTag(draft);
    }

    if (event.key === "Backspace" && !draft && values.length) {
      event.preventDefault();
      removeTag(values.length - 1);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-700">{label}</label>
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-orange-100 bg-white px-3 py-2 focus-within:border-orange-300 focus-within:ring-2 focus-within:ring-orange-100">
        {values.map((value, index) => (
          <span
            key={`${value}-${index}`}
            className="flex items-center gap-2 rounded-full bg-orange-50 px-3 py-1 text-xs font-medium text-orange-600"
          >
            {value}
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="rounded-full bg-white/0 p-1 text-orange-500 transition hover:bg-orange-100 hover:text-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-200"
              aria-label={`Remove ${value}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={values.length ? "Add more" : placeholder}
          className="min-w-[140px] flex-1 border-none bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-0"
        />
      </div>
      <p className="text-xs text-slate-400">
        Press Enter after each value, or use the × button to remove it.
      </p>
    </div>
  );
}
