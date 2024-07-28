import {
  ConfluenceIcon,
  FileIcon,
  GlobeIcon,

} from "@/components/icons/icons";
import { ValidSources } from "./types";
import { SourceCategory, SourceMetadata } from "./search/interfaces";

interface PartialSourceMetadata {
  icon: React.FC<{ size?: number; className?: string }>;
  displayName: string;
  category: SourceCategory;
}

type SourceMap = {
  [K in ValidSources]: PartialSourceMetadata;
};

const SOURCE_METADATA_MAP: SourceMap = {
  web: {
    icon: GlobeIcon,
    displayName: "Web",
    category: SourceCategory.ImportedKnowledge,
  },
  file: {
    icon: FileIcon,
    displayName: "File",
    category: SourceCategory.ImportedKnowledge,
  },
  
  confluence: {
    icon: ConfluenceIcon,
    displayName: "Confluence",
    category: SourceCategory.AppConnection,
  },
 
};

function fillSourceMetadata(
  partialMetadata: PartialSourceMetadata,
  internalName: ValidSources
): SourceMetadata {
  return {
    internalName: internalName,
    ...partialMetadata,
    adminUrl: `/admin/connectors/${partialMetadata.displayName
      .toLowerCase()
      .replaceAll(" ", "-")}`,
  };
}

export function getSourceMetadata(sourceType: ValidSources): SourceMetadata {
  return fillSourceMetadata(SOURCE_METADATA_MAP[sourceType], sourceType);
}

export function listSourceMetadata(): SourceMetadata[] {
  return Object.entries(SOURCE_METADATA_MAP).map(([source, metadata]) => {
    return fillSourceMetadata(metadata, source as ValidSources);
  });
}

export function getSourceDisplayName(sourceType: ValidSources): string | null {
  return getSourceMetadata(sourceType).displayName;
}
