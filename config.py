# Copyright 2025 Jose Gallego-Posada
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

ASSETS_DIR = Path.cwd() / "assets"
CLIPPINGS_DIR = ASSETS_DIR / "clippings"
PROCESSED_DIR = ASSETS_DIR / "processed"
LOGS_DIR = Path.cwd() / "logs"

KNOWN_COLORS = {
    "yellow": "#fff7aeea",
    "green": "#b6e4c7eb",
    "blue": "#aecbfac5",
    "red": "#f28b82ca",
    "purple": "#d7aefbd0",
    "gray": "#dbd6d6c8",
    "dark-gray": "#777777C9",
}
