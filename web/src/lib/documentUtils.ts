import { PayseraiDocument } from "./search/interfaces";

export function removeDuplicateDocs(documents: PayseraiDocument[]) {
  const seen = new Set<string>();
  const output: PayseraiDocument[] = [];
  documents.forEach((document) => {
    if (document.document_id && !seen.has(document.document_id)) {
      output.push(document);
      seen.add(document.document_id);
    }
  });
  return output;
}
