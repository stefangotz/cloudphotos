#!/bin/sh

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

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

curl -sSL https://install.python-poetry.org | python3 -
if ! poetry --help >/dev/null; then
    export PATH="$PATH:$HOME/.local/bin"
    echo 'export PATH="$PATH:$HOME/.local/bin"' >>~/.profile
fi
if ! poetry --help >/dev/null; then
    echo "Unable to invoke poetry; please install it manually and ensure it's on your path"
    exit 1
fi
poetry install
poetry run pre-commit install
