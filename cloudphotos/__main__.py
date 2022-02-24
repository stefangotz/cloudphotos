#!/usr/bin/env python3

# Copyright 2022 Stefan Götz <github.nooneelse@spamgourmet.com>

# This file is part of cloudphotos.

# cloudphotos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.

# cloudphotos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License along with cloudphotos. If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import List, Dict, Tuple
import json
import logging
import shutil
import subprocess
import sys

import exifread  # type: ignore
from pydantic import BaseModel
from pydantic.json import pydantic_encoder


_STATE_PATH: Path = Path.home() / "cloudphotos_state.json"


class CloudFile:
    def __init__(self, path: Path):
        self._path: Path = path
        self._mtime: float = 0.0
        self._md5: str = ""

    @property
    def path(self) -> Path:
        return self._path

    @property
    def mtime(self) -> float:
        if not self._mtime:
            self._mtime = self._path.stat().st_mtime
        return self._mtime

    @property
    def md5(self) -> str:
        if not self._md5:
            self._md5 = md5(self._path.open("rb").read()).hexdigest()
        return self._md5

    def __repr__(self):
        return f"CloudFile(path={self.path}, mtime={self.mtime}, md5={self.md5})"

    def copy_to_local(self, target_dir: Path, dir_suffix: str = ""):
        target_path = self._get_local_path(target_dir, dir_suffix)
        parent_dir: Path = target_path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True)

        if self._needs_conversion():
            subprocess.run(["magick", str(self.path), str(target_path)], check=True)
        else:
            shutil.copy2(self.path, target_path)

    def _get_local_path(self, target_dir: Path, dir_suffix: str = "") -> Path:
        suffix = self.path.suffix
        if suffix.lower() == ".heic":
            suffix = ".jpg"
        date = self._get_date()
        return (
            target_dir
            / f"{date.year}{dir_suffix}"
            / f"{date.year}-{date.month:02}{dir_suffix}"
            / (self.path.stem + suffix)
        )

    def _get_date(self) -> datetime:
        try:
            with self.path.open("rb") as image_file:
                tags = exifread.process_file(image_file)
                dto: str = tags["EXIF DateTimeOriginal"].values
                return datetime.strptime(dto, "%Y:%m:%d %H:%M:%S")
        except KeyError:
            logging.info("Unable to find EXIF DateTimeOriginal in %s", self)
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)
        return datetime.fromtimestamp(self.mtime)

    def _needs_conversion(self) -> bool:
        return self.path.suffix.lower().endswith("heic")


class FileModel(BaseModel):
    path: Path
    mtime: float
    md5: str


class FilesModel(BaseModel):
    files: List[FileModel]


class Files:
    def __init__(self, files_model: FilesModel):
        self._files: Dict[Tuple[str, str], FileModel] = {
            (mdl.path.name, mdl.md5): mdl for mdl in files_model.files
        }

    @staticmethod
    def load() -> "Files":
        if _STATE_PATH.exists():
            try:
                return Files(FilesModel.parse_file(_STATE_PATH))
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception(exc)
        return Files(FilesModel(files=[]))

    def store(self):
        with _STATE_PATH.open("w", encoding="UTF8") as file_desc:
            json.dump(self._get_model(), file_desc, default=pydantic_encoder)

    def _get_model(self):
        return FilesModel(files=list(self._files.values()))

    def add(self, cloud_file: CloudFile):
        self._files[(cloud_file.path.name, cloud_file.md5)] = FileModel(
            path=cloud_file.path, mtime=cloud_file.mtime, md5=cloud_file.md5
        )

    def contains(self, cloud_file: CloudFile) -> bool:
        return (cloud_file.path.name, cloud_file.md5) in self._files


def _main():
    logging.basicConfig(
        level=logging.INFO,
        filename=str(Path.home() / "cloudphotos.log"),
        format="%(asctime)s %(levelname)s:%(message)s",
    )

    source_dir = Path(sys.argv[1])
    assert source_dir.exists()
    target_dir = Path(sys.argv[2])
    assert target_dir.exists()
    dir_suffix = ""
    if len(sys.argv) > 3:
        dir_suffix = sys.argv[3]

    files = Files.load()
    for cloud_file in _yield_cloud_files(source_dir):
        try:
            if not files.contains(cloud_file):
                logging.info("The cloud_file %s hasn't been copied yet", cloud_file)
                cloud_file.copy_to_local(target_dir, dir_suffix)
                files.add(cloud_file)
                files.store()
                logging.info("Copied cloud_file %s", cloud_file)
            else:
                logging.info("The cloud_file %s has already been copied", cloud_file)
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)


def _yield_cloud_files(dir_path: Path):
    for child in dir_path.iterdir():
        if child.is_file():
            yield CloudFile(child)


if __name__ == "__main__":
    _main()
