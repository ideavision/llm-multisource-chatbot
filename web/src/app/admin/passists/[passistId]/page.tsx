import { ErrorCallout } from "@/components/ErrorCallout";
import { fetchSS } from "@/lib/utilsSS";
import { Passist } from "../interfaces";
import { PassistEditor } from "../PassistEditor";
import { DocumentSet } from "@/lib/types";
import { BackButton } from "@/components/BackButton";
import { Card, Title } from "@tremor/react";
import { DeletePassistButton } from "./DeletePassistButton";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";

export default async function Page({
  params,
}: {
  params: { passistId: string };
}) {
  const [
    passistResponse,
    documentSetsResponse,
    llmOverridesResponse,
    defaultLLMResponse,
  ] = await Promise.all([
    fetchSS(`/passist/${params.passistId}`),
    fetchSS("/manage/document-set"),
    fetchSS("/admin/passist/utils/list-available-models"),
    fetchSS("/admin/passist/utils/default-model"),
  ]);

  if (!passistResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch Passist - ${await passistResponse.text()}`}
      />
    );
  }

  if (!documentSetsResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch document sets - ${await documentSetsResponse.text()}`}
      />
    );
  }

  if (!llmOverridesResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch LLM override options - ${await documentSetsResponse.text()}`}
      />
    );
  }

  if (!defaultLLMResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch default LLM - ${await documentSetsResponse.text()}`}
      />
    );
  }

  const documentSets = (await documentSetsResponse.json()) as DocumentSet[];
  const passist = (await passistResponse.json()) as Passist;
  const llmOverrideOptions = (await llmOverridesResponse.json()) as string[];
  const defaultLLM = (await defaultLLMResponse.json()) as string;

  return (
    <div>
      <InstantSSRAutoRefresh />

      <BackButton />
      <div className="pb-2 mb-4 flex">
        <h1 className="text-3xl font-bold pl-2">Edit Passist</h1>
      </div>

      <Card>
        <PassistEditor
          existingPassist={passist}
          documentSets={documentSets}
          llmOverrideOptions={llmOverrideOptions}
          defaultLLM={defaultLLM}
        />
      </Card>

      <div className="mt-12">
        <Title>Delete Passist</Title>
        <div className="flex mt-6">
          <DeletePassistButton passistId={passist.id} />
        </div>
      </div>
    </div>
  );
}
