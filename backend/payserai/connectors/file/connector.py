import os
from collections.abc import Generator
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import IO

from payserai.configs.app_configs import INDEX_BATCH_SIZE
from payserai.configs.constants import DocumentSource
from payserai.connectors.cross_connector_utils.file_utils import detect_encoding
from payserai.connectors.cross_connector_utils.file_utils import load_files_from_zip
from payserai.connectors.cross_connector_utils.file_utils import read_file
from payserai.connectors.cross_connector_utils.file_utils import read_pdf_file
from payserai.connectors.cross_connector_utils.miscellaneous_utils import time_str_to_utc
from payserai.connectors.file.utils import check_file_ext_is_valid
from payserai.connectors.file.utils import get_file_ext
from payserai.connectors.interfaces import GenerateDocumentsOutput
from payserai.connectors.interfaces import LoadConnector
from payserai.connectors.models import Document
from payserai.connectors.models import Section
from payserai.utils.logger import setup_logger


logger = setup_logger()


def _open_files_at_location(
    file_path: str | Path,
) -> Generator[tuple[str, IO[Any]], Any, None]:
    extension = get_file_ext(file_path)

    if extension == ".zip":
        for file_info, file in load_files_from_zip(file_path, ignore_dirs=True):
            yield file_info.filename, file
    elif extension in [".txt", ".md", ".mdx"]:
        encoding = detect_encoding(file_path)
        with open(file_path, "r", encoding=encoding, errors="replace") as file:
            yield os.path.basename(file_path), file
    elif extension == ".pdf":
        with open(file_path, "rb") as file:
            yield os.path.basename(file_path), file
    else:
        logger.warning(f"Skipping file '{file_path}' with extension '{extension}'")


def _process_file(
    file_name: str,
    file: IO[Any],
    time_updated: datetime,
    pdf_pass: str | None = None,
) -> list[Document]:
    extension = get_file_ext(file_name)
    if not check_file_ext_is_valid(extension):
        logger.warning(f"Skipping file '{file_name}' with extension '{extension}'")
        return []

    metadata: dict[str, Any] = {}

    if extension == ".pdf":
        file_content_raw = read_pdf_file(
            file=file, file_name=file_name, pdf_pass=pdf_pass
        )
    else:
        file_content_raw, metadata = read_file(file)

    dt_str = metadata.get("doc_updated_at")
    final_time_updated = time_str_to_utc(dt_str) if dt_str else time_updated

    return [
        Document(
            id=file_name,
            sections=[
                Section(link=metadata.get("link"), text=file_content_raw.strip())
            ],
            source=DocumentSource.FILE,
            semantic_identifier=file_name,
            doc_updated_at=final_time_updated,
            primary_owners=metadata.get("primary_owners"),
            secondary_owners=metadata.get("secondary_owners"),
            metadata={},
        )
    ]


class LocalFileConnector(LoadConnector):
    def __init__(
        self,
        file_locations: list[Path | str],
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        self.file_locations = [Path(file_location) for file_location in file_locations]
        self.batch_size = batch_size
        self.pdf_pass: str | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        self.pdf_pass = credentials.get("pdf_password")
        return None

    def load_from_state(self) -> GenerateDocumentsOutput:
        documents: list[Document] = []
        for file_location in self.file_locations:
            current_datetime = datetime.now(timezone.utc)
            files = _open_files_at_location(file_location)

            for file_name, file in files:
                documents.extend(
                    _process_file(file_name, file, current_datetime, self.pdf_pass)
                )

                if len(documents) >= self.batch_size:
                    yield documents
                    documents = []

        if documents:
            yield documents


if __name__ == "__main__":
    connector = LocalFileConnector(file_locations=[os.environ["TEST_FILE"]])
    connector.load_credentials({"pdf_password": os.environ["PDF_PASSWORD"]})

    document_batches = connector.load_from_state()
    print(next(document_batches))
