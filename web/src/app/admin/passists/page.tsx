import { PassistsTable } from "./PassistTable";
import { FiPlusSquare } from "react-icons/fi";
import Link from "next/link";
import { Divider, Text, Title } from "@tremor/react";
import { fetchSS } from "@/lib/utilsSS";
import { ErrorCallout } from "@/components/ErrorCallout";
import { Passist } from "./interfaces";
import { BrainIcon } from "@/components/icons/icons";
import { AdminPageTitle } from "@/components/admin/Title";

export default async function Page() {
  const passistResponse = await fetchSS("/passist");

  if (!passistResponse.ok) {
    return (
      <ErrorCallout
        errorTitle="Something went wrong :("
        errorMsg={`Failed to fetch passists - ${await passistResponse.text()}`}
      />
    );
  }

  const passists = (await passistResponse.json()) as Passist[];

  return (
    <div className="mx-auto container">
      <AdminPageTitle icon={<BrainIcon size={32} />} title="Passists" />

      <Text className="mb-2">
        Passists are a way to build custom search/question-answering experiences
        for different use cases.
      </Text>
      <Text className="mt-2">They allow you to customize:</Text>
      <div className="text-sm">
        <ul className="list-disc mt-2 ml-4">
          <li>
            The prompt used by your LLM of choice to respond to the user query
          </li>
          <li>The documents that are used as context</li>
        </ul>
      </div>

      <div>
        <Divider />

        <Title>Create a Passist</Title>
        <Link
          href="/admin/passists/new"
          className="flex py-2 px-4 mt-2 border border-border h-fit cursor-pointer hover:bg-hover text-sm w-36"
        >
          <div className="mx-auto flex">
            <FiPlusSquare className="my-auto mr-2" />
            New Passist
          </div>
        </Link>

        <Divider />

        <Title>Existing Passists</Title>
        <PassistsTable passists={passists} />
      </div>
    </div>
  );
}
