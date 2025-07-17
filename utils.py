import re

from bs4 import BeautifulSoup

HIGHLIGHT_HEAD = """<mark style="background-color: yellow;">"""
HIGHLIGHT_TAIL = "</mark>"


def write_to_log(log_path, log):
    with open(log_path, "w", encoding="utf-8") as f:
        for line in log:
            f.write(line + "\n")


def interactive_choice(num_options, has_default=True, default_choice=0, prompt="Select an option"):
    default_str = f" (default is {default_choice})" if has_default else ""
    choice = input(f"\n{prompt}{default_str}: ")
    if has_default and choice == "":
        print(f"Using default choice: {default_choice}")
        choice = str(default_choice)
    while not choice.isdigit() or not (0 <= int(choice) < num_options):
        choice = input("Invalid input. Please enter a valid number: ")
        if has_default and choice == "":
            print(f"Using default choice: {default_choice}")
            choice = str(default_choice)

    return int(choice)


def normalize_str(s):
    # # Remove all kinds of whitespace and collapse to single space
    return re.sub(r"\s+", " ", s).strip()


def normalize_whitespace(s):
    # Unicode whitespace characters (excluding ASCII whitespace: space, tab, newline, etc.)
    unicode_whitespace = "".join(
        [
            "\u00a0",  # non-breaking space
            "\u1680",  # ogham space mark
            "\u180e",  # mongolian vowel separator
            "\u2000",
            "\u2001",
            "\u2002",
            "\u2003",
            "\u2004",
            "\u2005",
            "\u2006",
            "\u2007",
            "\u2008",
            "\u2009",
            "\u200a",  # various thin spaces
            "\u202f",  # narrow no-break space
            "\u205f",  # medium mathematical space
            "\u3000",  # ideographic space
            "\ufeff",  # byte order mark (zero-width non-breaking)
        ]
    )

    # Replace each Unicode whitespace character with a regular space
    pattern = f"[{re.escape(unicode_whitespace)}]"
    return re.sub(pattern, " ", s)


def min_window_subsequence(s, t):
    m, n = len(s), len(t)
    min_len = float("inf")
    start_idx = -1

    i = 0
    while i < m:
        # Step 1: Move `j` to match t
        if s[i] == t[0]:
            j = 0
            k = i
            while k < m:
                if s[k] == t[j]:
                    j += 1
                    if j == n:
                        break
                k += 1
            if j == n:
                # Step 2: Backtrack to minimize window
                end = k
                j -= 1
                while k >= i:
                    if s[k] == t[j]:
                        j -= 1
                        if j < 0:
                            break
                    k -= 1
                if end - k < min_len:
                    min_len = end - k
                    start_idx = k + 1
                i = k  # Continue from next position
        i += 1

    return s[start_idx - 1 : start_idx + min_len] if start_idx != -1 else ""


def split_raw_html_on_pars(html):
    # Regex to match either </p> or <p ...>
    pattern = r"(</p>|<p[^>]*>)"

    # Split and keep the delimiters
    parts = re.split(pattern, html)

    # Merge into desired structure: [chunk, </p>, <p...>, chunk, ...]
    result = []
    i = 0
    while i < len(parts):
        if parts[i].strip() != "":
            result.append(parts[i])
        i += 1

    return result


def create_highlighted_tags(match):
    prefix, suffix = match.all_tag_str.split(match.pre_highlight)
    html_tags = split_raw_html_on_pars(match.pre_highlight)

    to_insert = []
    for i, part in enumerate(html_tags):
        if i == 0:
            if part.startswith("<p") or part.startswith("</p>"):
                continue
            else:
                to_insert.append((i, HIGHLIGHT_HEAD))
        elif i > 0:
            if part.startswith("</p>"):
                to_insert.append((i, HIGHLIGHT_TAIL))
            elif part.startswith("<p") and html_tags[i - 1].endswith("</p>"):
                to_insert.append((i + 1, HIGHLIGHT_HEAD))
    if not (html_tags[-1].startswith("</p") or html_tags[-1].startswith("<p")):
        to_insert.append((len(html_tags), HIGHLIGHT_TAIL))

    # Count how many HIGHLIGHT_TAIL tags we have
    head_count = sum(1 for _ in to_insert if _[1] == HIGHLIGHT_HEAD)
    tail_count = sum(1 for _ in to_insert if _[1] == HIGHLIGHT_TAIL)
    assert head_count == tail_count, f"Mismatch in highlight tags: {head_count} heads and {tail_count} tails."

    # Insert the highlight tags in to_insert
    for offset, (i, tag) in enumerate(to_insert):
        html_tags.insert(offset + i, tag)

    if match.clip.note:
        note_tag = f'<span class="note" style="color: gray; font-style: italic; font-size: 90%;"> [R.N.: {match.clip.note}] </span>'
        html_tags.append(note_tag)

    new_soup = BeautifulSoup(prefix + "".join(html_tags) + suffix, "html.parser")
    new_tags = new_soup.find_all("p")

    return new_tags
