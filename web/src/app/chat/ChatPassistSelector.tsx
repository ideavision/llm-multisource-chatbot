import { Passist } from "@/app/admin/passists/interfaces";
import { FiCheck, FiChevronDown } from "react-icons/fi";
import { CustomDropdown } from "@/components/Dropdown";

function PassistItem({
  id,
  name,
  onSelect,
  isSelected,
}: {
  id: number;
  name: string;
  onSelect: (passistId: number) => void;
  isSelected: boolean;
}) {
  return (
    <div
      key={id}
      className={`
    flex
    px-3 
    text-sm 
    py-2 
    my-0.5
    rounded
    mx-1
    select-none 
    cursor-pointer 
    text-emphasis
    bg-background
    hover:bg-hover
  `}
      onClick={() => {
        onSelect(id);
      }}
    >
      {name}
      {isSelected && (
        <div className="ml-auto mr-1">
          <FiCheck />
        </div>
      )}
    </div>
  );
}

export function ChatPassistSelector({
  passists,
  selectedPassistId,
  onPassistChange,
}: {
  passists: Passist[];
  selectedPassistId: number | null;
  onPassistChange: (passist: Passist | null) => void;
}) {
  const currentlySelectedPassist = passists.find(
    (passist) => passist.id === selectedPassistId
  );

  return (
    <CustomDropdown
      dropdown={
        <div
          className={`
            border 
            border-border 
            bg-background
            rounded-lg 
            flex 
            flex-col 
            w-64 
            max-h-96 
            overflow-y-auto 
            flex
            overscroll-contain`}
        >
          {passists.map((passist, ind) => {
            const isSelected = passist.id === selectedPassistId;
            return (
              <PassistItem
                key={passist.id}
                id={passist.id}
                name={passist.name}
                onSelect={(clickedPassistId) => {
                  const clickedPassist = passists.find(
                    (passist) => passist.id === clickedPassistId
                  );
                  if (clickedPassist) {
                    onPassistChange(clickedPassist);
                  }
                }}
                isSelected={isSelected}
              />
            );
          })}
        </div>
      }
    >
      <div className="select-none text-xl font-bold flex px-2 py-1.5 text-strong rounded cursor-pointer hover:bg-hover-light">
        <div className="my-auto">
          {currentlySelectedPassist?.name || "Default"}
        </div>
        <FiChevronDown className="my-auto ml-1" />
      </div>
    </CustomDropdown>
  );
}
