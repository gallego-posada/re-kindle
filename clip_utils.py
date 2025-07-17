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


import argparse
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

import utils
from config import CLIPPINGS_DIR


class Clipping:
    pattern = re.compile(
        r"^(?P<type>Highlight|Note|- Your Highlight|- Your Note)"  # note/highlight type
        r"(?:\((?P<color>[^)]+)\))?"  # optional color
        r".*?Location (?P<location>\d+(?:-\d+)?)"  # full location or range
        r"(?:.*?Added on (?P<date>.+))?$",  # optional date
        re.IGNORECASE,
    )

    def process_metadata(self, metadata):
        match = self.pattern.match(metadata)
        if match:
            type = match.group("type").lower()
            type = "highlight" if "highlight" in type else "note" if "note" in type else None
            color = match.group("color")
            location = [int(_) for _ in match.group("location").split("-")]
            date = match.group("date").strip() if match.group("date") else None
            date = datetime.strptime(date, "%A, %B %d, %Y %I:%M:%S %p") if date else None

            self.type = type
            self.location = location
            self.date = date
            self.color = color
        else:
            raise ValueError(f"Invalid metadata format: {metadata}")

        if self.type == "note":
            assert len(self.location) == 1, "Notes should have a single location"

    def __init__(self, title, metadata, content):
        self.title = title
        self.process_metadata(metadata)
        self.note = None
        self.content = content

    def __repr__(self):
        if self.type == "highlight":
            return f"Highlight(location={self.location}, date={self.date})"
        elif self.type == "note":
            return f"Note(location={self.location}, date={self.date})"
        else:
            raise ValueError(f"Unknown clipping type: {self.type}")


def split_txt_clippings_by_title(filepath, clippings_dir):
    if not Path(filepath).is_file():
        raise FileNotFoundError(f"ERROR: cannot find {filepath}")

    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    # Remove BOM if present
    raw = raw.replace("\ufeff", "")

    clippings = raw.split("==========")
    all_clips = []

    for clip in clippings:
        lines = [line.strip() for line in clip.strip().split("\n") if line.strip()]
        if len(lines) < 3:
            continue

        if lines[2].strip():  # Last line is the highlight content
            all_clips.append(lines)

    # Group clips by title
    clips_by_title = {}
    for clip in all_clips:
        title = re.sub(r'[\\/*?:"<>|]', "", clip[0])
        if title not in clips_by_title:
            clips_by_title[title] = []
        clips_by_title[title].append(clip)

    # Write each title's clips to a separate file
    clippings_dir.mkdir(parents=True, exist_ok=True)
    for title, clips in clips_by_title.items():
        file_name = clippings_dir / f"{title}.txt"
        print(f"Writing {len(clips)} clips in {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            for clip in clips:
                f.write("\n".join(clip) + "\n==========\n")


def parse_txt_clippings(filepath, log_path=None):
    log = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    clippings = raw.split("==========")
    all_clips = []

    for clip in clippings:
        lines = [line.strip() for line in clip.strip().split("\n") if line.strip()]
        if len(lines) < 3:
            continue

        title, metadata, content = lines[0], lines[1], lines[2]

        if content.strip():
            clip = Clipping(title, metadata, content)
            all_clips.append(clip)

    parsed_clips = list(filter(lambda c: c.type == "highlight", all_clips))
    parsed_clips = sorted(parsed_clips, key=lambda c: c.date)

    parsed_notes = list(filter(lambda c: c.type == "note", all_clips))
    parsed_notes = sorted(parsed_notes, key=lambda c: c.date)

    for note in parsed_notes:
        # Find the latest highlight that matches the note's title and location
        for clip in reversed(parsed_clips):
            if clip.title == note.title and clip.location[-1] == note.location[0]:
                clip.note = note.content
                break

        warn_str = f"✘ Note '{note.content}' at location {note.location} could not be matched."
        log.append(warn_str)

    if log_path:
        utils.write_to_log(log_path, log)

    return parsed_clips


def parse_html_clippings(filepath, log_path=None):
    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    soup = BeautifulSoup(raw, "html.parser")
    title = soup.find("div", class_="bookTitle").get_text().strip()

    all_clips = []
    unpaired = []
    elements = soup.find_all(["div"])

    # TODO: I think HTML elements[0] might sometimes has all the highlights embedded in it

    i = 0
    while i < len(elements) - 1:
        if elements[i].get("class") == ["noteHeading"] and elements[i + 1].get("class") == ["noteText"]:
            metadata = elements[i].text.strip()
            content = elements[i + 1].text.strip()
            clip = Clipping(title, metadata, content)
            all_clips.append(clip)
            i += 2  # Skip the matched pair
        else:
            unpaired.append((i, elements[i]))
            i += 1  # Skip unpaired elements

    for ix in range(1, len(all_clips)):
        assert all_clips[ix - 1].location[0] <= all_clips[ix].location[0], (
            "Clippings not ordered by location. Note tagging may be incorrect."
        )

    note_indices = [ix for ix, clip in enumerate(all_clips) if clip.type == "note"]
    if len(note_indices) > 0:
        assert note_indices[0] > 0, "First clipping should not be a note."

        for note_ix in note_indices:
            note = all_clips[note_ix]
            clip = all_clips[note_ix - 1]
            clip.note = note.content

        parsed_clips = [clip for clip in all_clips if clip.type == "highlight"]
    else:
        parsed_clips = all_clips

    return parsed_clips


def parse_clippings(filepath, log_path=None):
    parsers = {".txt": parse_txt_clippings, ".html": parse_html_clippings}
    ext = filepath.suffix.lower()
    try:
        return parsers[ext](filepath, log_path)
    except KeyError:
        raise ValueError(f"Unsupported file format: {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse clippings from a file.")
    parser.add_argument(
        "--raw_clippings_path", required=True, type=str, help="Path to the raw exported clippings file."
    )
    parser.add_argument("--clippings_library_dir", type=str, help="Path to folder containing clippings files.")
    args = parser.parse_args()

    raw_clippings_path = args.raw_clippings_path

    clips_library_dir = args.clippings_library_dir
    if clips_library_dir is None:
        print("Using default clippings directory:", CLIPPINGS_DIR)
        clips_library_dir = CLIPPINGS_DIR

    split_txt_clippings_by_title(Path(raw_clippings_path), Path(clips_library_dir))
