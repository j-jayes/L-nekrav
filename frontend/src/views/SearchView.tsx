import type { Dispatch } from "react";
import type { Action, Selection } from "../lib/selection";
import type { AgeBand } from "../lib/urlState";

export type SearchViewProps = {
  selection: Selection;
  dispatch: Dispatch<Action>;
  age: AgeBand | null;
  setAge: (age: AgeBand | null) => void;
};

export function SearchView(_: SearchViewProps) {
  return <h2 className="text-xl font-semibold">Find the codes that fit a job</h2>;
}
