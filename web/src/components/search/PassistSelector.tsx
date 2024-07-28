import { Passist } from "@/app/admin/passists/interfaces";
import { CustomDropdown, DefaultDropdownElement } from "../Dropdown";
import { FiChevronDown } from "react-icons/fi";

export function PassistSelector({
  passists,
  selectedPassistId,
  onPassistChange,
}: {
  passists: Passist[];
  selectedPassistId: number;
  onPassistChange: (passist: Passist) => void;
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
              <DefaultDropdownElement
                key={passist.id}
                name={passist.name}
                onSelect={() => onPassistChange(passist)}
                isSelected={isSelected}
              />
            );
          })}
        </div>
      }
    >
      <div className="select-none text-sm font-bold flex text-emphasis px-2 py-1.5 cursor-pointer w-fit hover:bg-hover rounded">
        {currentlySelectedPassist?.name || "Default"}
        <FiChevronDown className="my-auto ml-2" />
      </div>
    </CustomDropdown>
  );
}
