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
import difflib
import os
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub
from tqdm import tqdm

import utils
from clip_utils import parse_clippings
from config import CLIPPINGS_DIR, KNOWN_COLORS, LOGS_DIR, PROCESSED_DIR


class Match:
    def __init__(self, clip, spine_ix, matched_tag_indices, all_tag_str, pre_highlight):
        self.clip = clip
        self.spine_ix = spine_ix
        self.matched_tag_indices = matched_tag_indices
        self.all_tag_str = all_tag_str
        self.pre_highlight = pre_highlight

    def __repr__(self):
        return f"Match(clip={self.clip}, spine_ix={self.spine_ix})"


def find_clip_in_spine(clip, spine, start_from=0):
    nospace_clip = "".join(clip.content.split(" "))
    for item_offset, item in enumerate(spine[start_from:]):
        soup = BeautifulSoup(item.get_content(), "xml")
        clean_soup = utils.normalize_str(soup.get_text())

        nospace_soup = "".join(clean_soup.split(" "))
        if nospace_clip in nospace_soup:
            item_ix = start_from + item_offset
            pars = soup.find_all("p")

            matched_tag_indices = find_text_spans(pars, clip.content)
            if matched_tag_indices is None:
                return None

            all_tag_str = "".join([str(pars[i]) for i in matched_tag_indices])
            all_tag_str = utils.normalize_whitespace(all_tag_str)

            pre_highlight = utils.min_window_subsequence(all_tag_str, nospace_clip)

            return Match(
                clip=clip,
                spine_ix=item_ix,
                matched_tag_indices=matched_tag_indices,
                all_tag_str=all_tag_str,
                pre_highlight=pre_highlight,
            )
    return None


def find_matches(clippings, ebook, log_path):
    spine = list(ebook.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    matches = []
    log = []

    for clip_ix in tqdm(range(len(clippings)), desc="Finding matches"):
        clip = clippings[clip_ix]
        clip_content = utils.normalize_str(clip.content)
        match = find_clip_in_spine(clip, spine)

        if match is None:
            log_str = f"✘ Not found: '{clip_content}'"
        else:
            log_str = f"✔ Found: '{clip_content}' in {spine[match.spine_ix].file_name}"
            matches.append(match)

        log.append(log_str)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for line in log:
            f.write(line + "\n")

    if len(matches) < len(clippings):
        Warning(f"Only {len(matches)} out of {len(clippings)} highlights found. Check highlight_log.txt for details.")

    return matches


def find_text_spans(elements, query):
    norm_query = utils.normalize_str(query)
    full_texts = [utils.normalize_str(el.get_text()) for el in elements]

    combined = ""
    spans = []
    for text in full_texts:
        if combined:
            combined += " "
        start = len(combined)
        combined += text
        end = len(combined)
        spans.append((start, end))

    start_pos = combined.find(norm_query)
    if start_pos == -1:
        return None

    end_pos = start_pos + len(norm_query)

    matched_indices = []
    for i, (start, end) in enumerate(spans):
        if end <= start_pos:
            continue
        if start >= end_pos:
            break
        matched_indices.append(i)

    return matched_indices


def list_known_clippings(
    book_name,
    clippings_library_dir,
    do_clippings_title_matching=True,
    pre_fetch_clippings=True,
):
    if do_clippings_title_matching:
        # Fuzzy match clippings to ebook_name
        matched_clippings = difflib.get_close_matches(book_name, os.listdir(clippings_library_dir), n=3, cutoff=0.5)
    else:
        matched_clippings = [file for file in os.listdir(clippings_library_dir) if file.endswith((".txt", ".html"))]

    if len(matched_clippings) == 0:
        print(f"No matching clippings files found for book '{book_name}'.")
        exit(1)

    pre_fetched_clippings = []
    if pre_fetch_clippings:
        for matched_path in matched_clippings:
            clips_path = clippings_library_dir / matched_path
            try:
                clippings = parse_clippings(clips_path, log_path=None)
                pre_fetched_clippings.append(clippings)
            except Exception as e:
                print(f"Error parsing clippings file {matched_path}: {e}")
                pre_fetched_clippings.append(None)

        # Sort in descending number of highlights/notes for easy selection of most relevant
        pre_fetched_clippings = sorted(pre_fetched_clippings, key=lambda x: len(x) if x else 0, reverse=True)
        matched_clippings = sorted(
            matched_clippings, key=lambda x: len(pre_fetched_clippings[matched_clippings.index(x)])
        )

    if do_clippings_title_matching:
        print(f"\n💽 Available clippings in '{clippings_library_dir}' matching EPUB name:")
    else:
        print(f"\n💽 Available clippings files in '{clippings_library_dir}':")
    for file_number, clip_file in enumerate(matched_clippings):
        display_str = f"- [{file_number}] {clip_file}"
        if pre_fetch_clippings:
            pre_fetched = pre_fetched_clippings[file_number]
            num_elements = len(pre_fetched) if pre_fetched else "N/A"
            display_str += f" [{num_elements} highlights/notes]"
        print(display_str)

    choice = utils.interactive_choice(
        len(matched_clippings), has_default=True, default_choice=0, prompt="Select your clippings file"
    )

    clips_path = matched_clippings[choice]
    clippings = pre_fetched_clippings[choice] if pre_fetch_clippings else None

    return clippings_library_dir / clips_path, clippings


def list_known_epubs(ebook_library_dir):
    # List all EPUB files found (recursively) in the given path
    epub_files = []
    for root, dirs, files in os.walk(ebook_library_dir):
        # Skip hidden folders
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.endswith(".epub") and not file.startswith("."):
                epub_files.append((file, os.path.join(root, file)))

    if len(epub_files) == 0:
        print(f"No EPUB files found in {ebook_library_dir}.")
        exit(1)

    # Sort EPUBs alphabetically by their names
    epub_files.sort(key=lambda x: x[0].lower())

    print(f"\n💽 Available source EPUBs under '{ebook_library_dir}':")
    for file_number, (short_name, _) in enumerate(epub_files):
        print(f"- [{file_number}] {short_name}")

    epub_choice = utils.interactive_choice(len(epub_files), has_default=False, prompt="Select your source EPUB")
    return epub_files[epub_choice][-1]


def process_book(
    ebook_path,
    clips_path=None,
    clippings_library_dir=None,
    do_clippings_title_matching=True,
    pre_fetch_clippings=True,
    highlight_color=None,
):
    if os.path.exists(ebook_path):
        filename = os.path.basename(ebook_path)
        book_name = os.path.splitext(filename)[0]  # Remove .epub extension
    else:
        raise FileNotFoundError(f"EPUB file '{ebook_path}' does not exist.")

    print(f"📖 Processing book '{book_name}'")
    log_path = LOGS_DIR / f"{book_name}_log.txt"

    clippings = None
    if clips_path is None:
        clips_path, clippings = list_known_clippings(
            book_name,
            clippings_library_dir,
            do_clippings_title_matching=do_clippings_title_matching,
            pre_fetch_clippings=pre_fetch_clippings,
        )
    if clippings is None:
        clippings = parse_clippings(clips_path, log_path=log_path)

    ebook = epub.read_epub(ebook_path)
    spine = list(ebook.get_items_of_type(ebooklib.ITEM_DOCUMENT))

    matches = find_matches(clippings, ebook, log_path=log_path)

    for match in tqdm(matches, desc="Applying highlights"):
        raw_item = spine[match.spine_ix]
        soup = BeautifulSoup(raw_item.get_content(), "xml")
        pars = soup.find_all("p")
        new_tags = utils.create_highlighted_tags(match, highlight_color=highlight_color)

        for ix, orig_ix in enumerate(match.matched_tag_indices):
            pars[orig_ix].replace_with(new_tags[ix])

        raw_item.set_content(str(soup).encode("utf-8"))

    # Write the modified EPUB back to disk
    processed_path = PROCESSED_DIR / f"{book_name}.epub"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(processed_path, ebook)

    print(f"\n✅ Done - {len(matches)}/{len(clippings)} highlights applied.")
    print(f"📄 Log saved to '{log_path}'")
    if len(matches) < len(clippings):
        print(f"⚠️  Did not locate {len(clippings) - len(matches)} highlights. Check '{log_path}' for details.")
    print(f"\n💾 Highlighted EPUB saved to '{processed_path}'")


def argparse_setup():
    parser = argparse.ArgumentParser(description="Re-kindle highlights and notes into an EPUB file.")
    parser.add_argument("--ebook_path", type=str, help="Path to a specific EPUB file.")
    parser.add_argument("--ebook_library_dir", type=str, help="Path to folder containing EPUB files.")
    parser.add_argument(
        "--use_calibre_library", action="store_true", help="Use default location of Calibre library to fetch EPUBs."
    )

    parser.add_argument("--clippings_path", type=str, help="Path to a specific clippings file.")
    parser.add_argument("--clippings_library_dir", type=str, help="Path to folder containing clippings files.")

    parser.add_argument(
        "--smart_title_matching",
        action="store_true",
        help="List only relevant clippings files based on the EPUB title.",
    )
    parser.add_argument(
        "--pre_fetch_clippings",
        action="store_true",
        help="Pre-fetch number elements in a clippings file for more intuitive navigation.",
    )

    parser.add_argument("--highlight_color", type=str, help="Color to use for highlights (default: gray).")

    return parser


if __name__ == "__main__":
    parser = argparse_setup()
    args = parser.parse_args()

    ebook_path = Path(args.ebook_path) if args.ebook_path else None
    if ebook_path is None:
        if args.use_calibre_library:
            ebook_library_dir = Path.home() / "Calibre Library"
        else:
            assert args.ebook_library_dir is not None, "You must provide either --ebook_path or --ebook_library_dir."
            ebook_library_dir = Path(args.ebook_library_dir)
        ebook_path = list_known_epubs(ebook_library_dir)

    clips_path = Path(args.clippings_path) if args.clippings_path else None

    clips_library_dir = args.clippings_library_dir
    if clips_path is None and args.clippings_library_dir is None:
        print("Using default clippings directory:", CLIPPINGS_DIR)
        clips_library_dir = CLIPPINGS_DIR
    if clips_library_dir is not None:
        clips_library_dir = Path(clips_library_dir)

    if args.highlight_color is None:
        highlight_color = KNOWN_COLORS.get("yellow")
    elif args.highlight_color in KNOWN_COLORS:
        highlight_color = KNOWN_COLORS[args.highlight_color]
    elif utils.is_valid_hex_color(args.highlight_color):
        highlight_color = args.highlight_color
    else:
        raise ValueError(
            f"Invalid highlight color: {args.highlight_color}. Must be one of {list(KNOWN_COLORS.keys())} or a valid hex color code."
        )

    process_book(
        ebook_path=ebook_path,
        clips_path=clips_path,
        clippings_library_dir=clips_library_dir,
        do_clippings_title_matching=args.smart_title_matching,
        pre_fetch_clippings=args.pre_fetch_clippings,
        highlight_color=highlight_color,
    )
