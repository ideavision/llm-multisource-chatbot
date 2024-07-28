import { listSourceMetadata } from "@/lib/sources";
import { ValidSources } from "@/lib/types";
import Image from "next/image";
import { Passist } from "../admin/passists/interfaces";
import { Divider } from "@tremor/react";
import { FiBookmark, FiCpu, FiInfo, FiX, FiZoomIn } from "react-icons/fi";
import { HoverPopup } from "@/components/HoverPopup";
import { Modal } from "@/components/Modal";
import { useState } from "react";
import { FaRobot } from "react-icons/fa";

const MAX_PERSONAS_TO_DISPLAY = 4;

function HelperItemDisplay({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="cursor-default  bg-gray-100 hover:bg-hover-light border border-border rounded py-2 px-4">
      <div className="text-emphasis font-bold text-lg flex">{title}</div>
      <div className="text-sm">{description}</div>
    </div>
  );
}

function AllPassistOptionDisplay({
  availablePassists,
  handlePassistSelect,
  handleClose,
}: {
  availablePassists: Passist[];
  handlePassistSelect: (passist: Passist) => void;
  handleClose: () => void;
}) {
  return (
    <Modal onOutsideClick={handleClose}>
      <div className="px-8 py-12">
        <div className="flex w-full border-b border-border mb-4 pb-4">
          <h2 className="text-xl text-strong font-bold flex">
            <div className="p-1 bg-ai rounded-lg h-fit my-auto mr-2">
              <div className="text-inverted">
                <FiCpu size={16} className="my-auto mx-auto" />
              </div>
            </div>
            All Available Assistants
          </h2>

          <div
            onClick={handleClose}
            className="ml-auto p-1 rounded hover:bg-hover"
          >
            <FiX size={18} />
          </div>
        </div>
        <div className="flex flex-col gap-y-4 max-h-96 overflow-y-auto pb-4 px-2">
          {availablePassists.map((passist) => (
            <div
              key={passist.id}
              onClick={() => {
                handleClose();
                handlePassistSelect(passist);
              }}
            >
              <HelperItemDisplay
                title={passist.name}
                description={passist.description}
              />
            </div>
          ))}
        </div>
      </div>
    </Modal>
  );
}

export function ChatIntro({
  availableSources,
  availablePassists,
  selectedPassist,
  handlePassistSelect,
}: {
  availableSources: ValidSources[];
  availablePassists: Passist[];
  selectedPassist?: Passist;
  handlePassistSelect: (passist: Passist) => void;
}) {
  const [isAllPassistOptionVisible, setIsAllPassistOptionVisible] =
    useState(false);

  const allSources = listSourceMetadata();
  const availableSourceMetadata = allSources.filter((source) =>
    availableSources.includes(source.internalName)
  );

  return (
    <>
      {isAllPassistOptionVisible && (
        <AllPassistOptionDisplay
          handleClose={() => setIsAllPassistOptionVisible(false)}
          availablePassists={availablePassists}
          handlePassistSelect={handlePassistSelect}
        />
      )}
      <div className="flex justify-center items-center h-full">
        {selectedPassist ? (
          <div className="w-message-xs 2xl:w-message-sm 3xl:w-message">
            <div className="flex">
              <div className="mx-auto">
                <div className="m-auto h-[60px] w-[180px]">
                  <Image
                    src="/logo.png"
                    alt="Logo"
                    width="1419"
                    height="1520"
                  />
                </div>
                <div className="mx-auto text-2xl font-light antialiased p-4 w-fit">
                  {selectedPassist?.name || "How can I help you today?"}
                </div>
                {selectedPassist && (
                  <div className="mt-1">{selectedPassist.description}</div>
                )}
              </div>
            </div>

            <Divider />
            <div>
              {selectedPassist && selectedPassist.document_sets.length > 0 && (
                <div className="mt-2">
                  <p className="font-bold mb-1 mt-4 text-emphasis">
                    Knowledge Sets:{" "}
                  </p>
                  {selectedPassist.document_sets.map((documentSet) => (
                    <div key={documentSet.id} className="w-fit">
                      <HoverPopup
                        mainContent={
                          <span className="flex w-fit p-1 rounded border border-border text-xs font-medium cursor-default">
                            <div className="mr-1 my-auto">
                              <FiBookmark />
                            </div>
                            {documentSet.name}
                          </span>
                        }
                        popupContent={
                          <div className="flex py-1 w-96">
                            <FiInfo className="my-auto mr-2" />
                            <div className="text-sm">
                              {documentSet.description}
                            </div>
                          </div>
                        }
                        direction="top"
                      />
                    </div>
                  ))}
                </div>
              )}
              {availableSources.length > 0 && (
                <div className="mt-2">
                  <p className="font-bold mb-1 mt-4 text-emphasis">
                    Connected Sources:{" "}
                  </p>
                  <div className="flex flex-wrap gap-x-2">
                    {availableSourceMetadata.map((sourceMetadata) => (
                      <span
                        key={sourceMetadata.internalName}
                        className="flex w-fit p-1 rounded border border-border text-xs font-medium cursor-default"
                      >
                        <div className="mr-1 my-auto">
                          {sourceMetadata.icon({})}
                        </div>
                        {sourceMetadata.displayName}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="px-12 w-searchbar-xs 2xl:w-searchbar-sm 3xl:w-searchbar">
            <div className="mx-auto">
              <div className="m-auto h-[60px] w-[180px]">
                <Image src="/logo.png" alt="Logo" width="1419" height="1520" />
              </div>
            </div>

            <div className="mt-2">
              <p className="mx-auto text-2xl font-light antialiased p-4 w-fit">
                Which assistant do you want to chat with today?{" "}
              </p>
              <p className="text-sm text-center">
                Or ask a question immediately to use the{" "}
                <b>{availablePassists[0]?.name}</b> assistant.
              </p>
              <div className="flex flex-col gap-y-4 mt-8">
                {availablePassists
                  .slice(0, MAX_PERSONAS_TO_DISPLAY)
                  .map((passist) => (
                    <div
                      key={passist.id}
                      onClick={() => handlePassistSelect(passist)}
                    >
                      <HelperItemDisplay
                        title={passist.name}
                        description={passist.description}
                      />
                    </div>
                  ))}
              </div>
              {availablePassists.length > MAX_PERSONAS_TO_DISPLAY && (
                <div className="mt-4 flex">
                  <div
                    onClick={() => setIsAllPassistOptionVisible(true)}
                    className="text-sm flex mx-auto p-1 hover:bg-hover-light rounded cursor-default"
                  >
                    <FiZoomIn className="my-auto mr-1" /> See more
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
