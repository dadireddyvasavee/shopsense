import { useEffect, useState } from "react";

const KEY = "compare-tray";
const read = (): number[] => JSON.parse(localStorage.getItem(KEY) || "[]");
export function useCompareTray() {
  const [ids, setIds] = useState<number[]>(read);
  useEffect(() => { const h = () => setIds(read()); window.addEventListener("tray", h); return () => window.removeEventListener("tray", h); }, []);
  const write = (v: number[]) => { localStorage.setItem(KEY, JSON.stringify(v)); window.dispatchEvent(new Event("tray")); };
  return {
    ids,
    toggle: (id: number) => write(ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id].slice(-4)),
    clear: () => write([]),
  };
}
