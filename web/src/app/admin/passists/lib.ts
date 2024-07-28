import { Passist, Prompt } from "./interfaces";

interface PassistCreationRequest {
  name: string;
  description: string;
  system_prompt: string;
  task_prompt: string;
  document_set_ids: number[];
  num_chunks: number | null;
  llm_relevance_filter: boolean | null;
  llm_model_version_override: string | null;
}

interface PassistUpdateRequest {
  id: number;
  existingPromptId: number | undefined;
  name: string;
  description: string;
  system_prompt: string;
  task_prompt: string;
  document_set_ids: number[];
  num_chunks: number | null;
  llm_relevance_filter: boolean | null;
  llm_model_version_override: string | null;
}

function promptNameFromPassistName(passistName: string) {
  return `default-prompt__${passistName}`;
}

function createPrompt({
  passistName,
  systemPrompt,
  taskPrompt,
}: {
  passistName: string;
  systemPrompt: string;
  taskPrompt: string;
}) {
  return fetch("/api/prompt", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: promptNameFromPassistName(passistName),
      description: `Default prompt for passist ${passistName}`,
      shared: true,
      system_prompt: systemPrompt,
      task_prompt: taskPrompt,
    }),
  });
}

function updatePrompt({
  promptId,
  passistName,
  systemPrompt,
  taskPrompt,
}: {
  promptId: number;
  passistName: string;
  systemPrompt: string;
  taskPrompt: string;
}) {
  return fetch(`/api/prompt/${promptId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: promptNameFromPassistName(passistName),
      description: `Default prompt for passist ${passistName}`,
      shared: true,
      system_prompt: systemPrompt,
      task_prompt: taskPrompt,
    }),
  });
}

function buildPassistAPIBody(
  creationRequest: PassistCreationRequest | PassistUpdateRequest,
  promptId: number
) {
  const {
    name,
    description,
    document_set_ids,
    num_chunks,
    llm_relevance_filter,
  } = creationRequest;

  return {
    name,
    description,
    shared: true,
    num_chunks,
    llm_relevance_filter,
    llm_filter_extraction: false,
    recency_bias: "base_decay",
    prompt_ids: [promptId],
    document_set_ids,
    llm_model_version_override: creationRequest.llm_model_version_override,
  };
}

export async function createPassist(
  passistCreationRequest: PassistCreationRequest
): Promise<[Response, Response | null]> {
  // first create prompt
  const createPromptResponse = await createPrompt({
    passistName: passistCreationRequest.name,
    systemPrompt: passistCreationRequest.system_prompt,
    taskPrompt: passistCreationRequest.task_prompt,
  });
  const promptId = createPromptResponse.ok
    ? (await createPromptResponse.json()).id
    : null;

  const createPassistResponse =
    promptId !== null
      ? await fetch("/api/admin/passist", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(
            buildPassistAPIBody(passistCreationRequest, promptId)
          ),
        })
      : null;

  return [createPromptResponse, createPassistResponse];
}

export async function updatePassist(
  passistUpdateRequest: PassistUpdateRequest
): Promise<[Response, Response | null]> {
  const { id, existingPromptId } = passistUpdateRequest;

  // first update prompt
  let promptResponse;
  let promptId;
  if (existingPromptId !== undefined) {
    promptResponse = await updatePrompt({
      promptId: existingPromptId,
      passistName: passistUpdateRequest.name,
      systemPrompt: passistUpdateRequest.system_prompt,
      taskPrompt: passistUpdateRequest.task_prompt,
    });
    promptId = existingPromptId;
  } else {
    promptResponse = await createPrompt({
      passistName: passistUpdateRequest.name,
      systemPrompt: passistUpdateRequest.system_prompt,
      taskPrompt: passistUpdateRequest.task_prompt,
    });
    promptId = promptResponse.ok ? (await promptResponse.json()).id : null;
  }

  const updatePassistResponse =
    promptResponse.ok && promptId
      ? await fetch(`/api/admin/passist/${id}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(
            buildPassistAPIBody(passistUpdateRequest, promptId)
          ),
        })
      : null;

  return [promptResponse, updatePassistResponse];
}

export function deletePassist(passistId: number) {
  return fetch(`/api/admin/passist/${passistId}`, {
    method: "DELETE",
  });
}

export function buildFinalPrompt(
  systemPrompt: string,
  taskPrompt: string,
  retrievalDisabled: boolean
) {
  let queryString = Object.entries({
    system_prompt: systemPrompt,
    task_prompt: taskPrompt,
    retrieval_disabled: retrievalDisabled,
  })
    .map(
      ([key, value]) =>
        `${encodeURIComponent(key)}=${encodeURIComponent(value)}`
    )
    .join("&");

  return fetch(`/api/passist/utils/prompt-explorer?${queryString}`);
}

function smallerNumberFirstComparator(a: number, b: number) {
  return a > b ? 1 : -1;
}

export function passistComparator(a: Passist, b: Passist) {
  if (a.display_priority === null && b.display_priority === null) {
    return smallerNumberFirstComparator(a.id, b.id);
  }

  if (a.display_priority !== b.display_priority) {
    if (a.display_priority === null) {
      return 1;
    }
    if (b.display_priority === null) {
      return -1;
    }

    return smallerNumberFirstComparator(a.display_priority, b.display_priority);
  }

  return smallerNumberFirstComparator(a.id, b.id);
}
