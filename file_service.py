import asyncssh
import logging
from nodes import Node
import asyncio
import os, shutil

SDFS_LOCATION = "./sdfs/"
MAX_FILE_VERSIONS = 5

CLEANUP_ON_STARTUP = False

class FileService:

    def __init__(self) -> None:
        self.current_files = {}
        if CLEANUP_ON_STARTUP:
            self.cleanup_all_files()

    def load_files_from_directory(self):
        pass

    def list_all_files(self):
        for key, value in self.current_files.items():
            print(f"{key}: {len(value)}")
    
    def cleanup_all_files(self):
        for filename in os.listdir(SDFS_LOCATION):
            file_path = os.path.join(SDFS_LOCATION, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logging.error(f'Failed to delete {file_path}. Reason: {e}')

    async def download_file(self, host: str, username: str, password: str, file_location: str, filename: str) -> None:
        
        destination_file = ""
        if filename in self.current_files:
            # file is already present
            file_list = self.current_files[filename]
            current_latest_filename: str = file_list[-1]
            pos = current_latest_filename.rfind("_")
            version = int(current_latest_filename[pos + len("_version"):])
            destination_file = f"{filename}_version{version + 1}"
        else:
            destination_file = f"{filename}_version1"

        try:
            async with asyncssh.connect(host, username=username, password=password) as conn:
                await asyncssh.scp((conn, file_location), SDFS_LOCATION + destination_file)
            
            # saved file successfully add it to the dict
            if filename in self.current_files:
                self.current_files[filename].append(destination_file)
                if len(self.current_files[filename]) > MAX_FILE_VERSIONS:
                    os.remove(SDFS_LOCATION + self.current_files[filename][0])
                    del self.current_files[filename][0]
            else:
                self.current_files[filename] = [destination_file]
            
            self.list_all_files()

            return True
        except (OSError, asyncssh.Error) as exc:
            logging.error(f'Failed to download file {file_location} from {host}: {str(exc)}')
            return False
