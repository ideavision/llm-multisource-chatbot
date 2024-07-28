"use client";

import { Divider, Text } from "@tremor/react";
import { Passist } from "./interfaces";
import { EditButton } from "@/components/EditButton";
import { useRouter } from "next/navigation";
import { CustomCheckbox } from "@/components/CustomCheckbox";
import { usePopup } from "@/components/admin/connectors/Popup";
import { useState } from "react";
import { UniqueIdentifier } from "@dnd-kit/core";
import { DraggableTable } from "@/components/table/DraggableTable";
import { passistComparator } from "./lib";

export function PassistsTable({ passists }: { passists: Passist[] }) {
  const router = useRouter();
  const { popup, setPopup } = usePopup();

  const sortedPassists = [...passists];
  sortedPassists.sort(passistComparator);

  const [finalPassists, setFinalPassists] = useState<UniqueIdentifier[]>(
    sortedPassists.map((passist) => passist.id.toString())
  );
  const finalPassistValues = finalPassists.map((id) => {
    return sortedPassists.find(
      (passist) => passist.id.toString() === id
    ) as Passist;
  });

  const updatePassistOrder = async (orderedPassistIds: UniqueIdentifier[]) => {
    setFinalPassists(orderedPassistIds);

    const displayPriorityMap = new Map<UniqueIdentifier, number>();
    orderedPassistIds.forEach((passistId, ind) => {
      displayPriorityMap.set(passistId, ind);
    });

    const response = await fetch("/api/admin/passist/display-priority", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        display_priority_map: Object.fromEntries(displayPriorityMap),
      }),
    });
    if (!response.ok) {
      setPopup({
        type: "error",
        message: `Failed to update passist order - ${await response.text()}`,
      });
      router.refresh();
    }
  };

  return (
    <div>
      {popup}

      <Text className="my-2">
        Passists will be displayed as options on the Chat / Search interfaces in
        the order they are displayed below. Passists marked as hidden will not
        be displayed.
      </Text>

      <DraggableTable
        headers={["Name", "Description", "Built-In", "Is Visible", ""]}
        rows={finalPassistValues.map((passist) => {
          return {
            id: passist.id.toString(),
            cells: [
              <p
                key="name"
                className="text font-medium whitespace-normal break-none"
              >
                {passist.name}
              </p>,
              <p
                key="description"
                className="whitespace-normal break-all max-w-2xl"
              >
                {passist.description}
              </p>,
              passist.default_passist ? "Yes" : "No",
              <div
                key="is_visible"
                onClick={async () => {
                  const response = await fetch(
                    `/api/admin/passist/${passist.id}/visible`,
                    {
                      method: "PATCH",
                      headers: {
                        "Content-Type": "application/json",
                      },
                      body: JSON.stringify({
                        is_visible: !passist.is_visible,
                      }),
                    }
                  );
                  if (response.ok) {
                    router.refresh();
                  } else {
                    setPopup({
                      type: "error",
                      message: `Failed to update passist - ${await response.text()}`,
                    });
                  }
                }}
                className="px-1 py-0.5 hover:bg-hover-light rounded flex cursor-pointer select-none w-fit"
              >
                <div className="my-auto w-12">
                  {!passist.is_visible ? (
                    <div className="text-error">Hidden</div>
                  ) : (
                    "Visible"
                  )}
                </div>
                <div className="ml-1 my-auto">
                  <CustomCheckbox checked={passist.is_visible} />
                </div>
              </div>,
              <div key="edit" className="flex">
                <div className="mx-auto">
                  {!passist.default_passist ? (
                    <EditButton
                      onClick={() =>
                        router.push(`/admin/passists/${passist.id}`)
                      }
                    />
                  ) : (
                    "-"
                  )}
                </div>
              </div>,
            ],
            staticModifiers: [[1, "lg:w-[300px] xl:w-[400px] 2xl:w-[550px]"]],
          };
        })}
        setRows={updatePassistOrder}
      />

      <Divider />

      {/* <TableBody>
          {sortedPassists.map((passist) => {
            return (
              <DraggableRow key={passist.id}>
                <TableCell className="whitespace-normal break-none">
                  <p className="text font-medium">{passist.name}</p>
                </TableCell>
                <TableCell className="whitespace-normal break-all max-w-2xl">
                  {passist.description}
                </TableCell>
                <TableCell>{passist.default_passist ? "Yes" : "No"}</TableCell>
                <TableCell>
                  {" "}
                  <div
                    onClick={async () => {
                      const response = await fetch(
                        `/api/admin/passist/${passist.id}/visible`,
                        {
                          method: "PATCH",
                          headers: {
                            "Content-Type": "application/json",
                          },
                          body: JSON.stringify({
                            is_visible: !passist.is_visible,
                          }),
                        }
                      );
                      if (response.ok) {
                        router.refresh();
                      } else {
                        setPopup({
                          type: "error",
                          message: `Failed to update passist - ${await response.text()}`,
                        });
                      }
                    }}
                    className="px-1 py-0.5 hover:bg-hover-light rounded flex cursor-pointer select-none w-fit"
                  >
                    <div className="my-auto w-12">
                      {!passist.is_visible ? (
                        <div className="text-error">Hidden</div>
                      ) : (
                        "Visible"
                      )}
                    </div>
                    <div className="ml-1 my-auto">
                      <CustomCheckbox checked={passist.is_visible} />
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  {passist.is_visible ? (
                    <EditableValue
                      emptyDisplay="-"
                      initialValue={
                        passist.display_priority !== null
                          ? passist.display_priority.toString()
                          : ""
                      }
                      onSubmit={async (value) => {
                        if (
                          value === (passist.display_priority || "").toString()
                        ) {
                          return true;
                        }

                        const numericDisplayPriority = Number(value);
                        if (isNaN(numericDisplayPriority)) {
                          setPopup({
                            message: "Display priority must be a number",
                            type: "error",
                          });
                          return false;
                        }

                        const response = await fetch(
                          `/api/admin/passist/${passist.id}/display-priority`,
                          {
                            method: "PATCH",
                            headers: {
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                              display_priority: numericDisplayPriority,
                            }),
                          }
                        );
                        if (!response.ok) {
                          setPopup({
                            message: `Failed to update display priority - ${await response.text()}`,
                            type: "error",
                          });
                        }
                        
                        router.refresh();
                        return true;
                      }}
                    />
                  ) : (
                    "-"
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex">
                    <div className="mx-auto">
                      {!passist.default_passist ? (
                        <EditButton
                          onClick={() =>
                            router.push(`/admin/passists/${passist.id}`)
                          }
                        />
                      ) : (
                        "-"
                      )}
                    </div>
                  </div>
                </TableCell>
              </DraggableRow>
            );
          })}
        </TableBody> */}
    </div>
  );
}
