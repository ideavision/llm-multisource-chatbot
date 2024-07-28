"use client";

import { Button } from "@tremor/react";
import { FiTrash } from "react-icons/fi";
import { deletePassist } from "../lib";
import { useRouter } from "next/navigation";

export function DeletePassistButton({ passistId }: { passistId: number }) {
  const router = useRouter();

  return (
    <Button
      size="xs"
      color="red"
      onClick={async () => {
        const response = await deletePassist(passistId);
        if (response.ok) {
          router.push(`/admin/passists?u=${Date.now()}`);
        } else {
          alert(`Failed to delete passist - ${await response.text()}`);
        }
      }}
      icon={FiTrash}
    >
      Delete
    </Button>
  );
}
