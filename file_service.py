import asyncssh
import logging
from nodes import Node
import asyncio


class FileService:

    def __init__(self) -> None:
        current_files = {}

    def load_files_from_directory(self):
        pass

    def check_for_file(self, filename):
        pass

    def get_download_location_for_file(self, filename: str):

        escaped_filename = filename.replace("/", "_")
        escaped_filename = escaped_filename.replace(".", "_")

        # check if 

        pass

    def download_complete_for_file(self, filename):
        pass

    def clear_all_files(self):
        pass

    async def download_file(self, host: str, username: str, password: str, file_location: str, dest_location: str) -> None:
        try:
            async with asyncssh.connect(host, username=username, password=password) as conn:
                await asyncssh.scp((conn, file_location), dest_location)
            return True
        except (OSError, asyncssh.Error) as exc:
            logging.error(f'Failed to download file {file_location} from {host}: {str(exc)}')
            return False
