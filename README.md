# re:kindle 🔥
`re:kindle` is a light-weight Python tool for re-integrating highlights exported from Kindle back into your EPUBs.

<p align="center">
    <img src="re_kindle_banner.png" alt="re:kindle"/>
</p>

## How to use `re:kindle`

### 📦 Installation
`re:kindle` is written for Python 3. You can install the dependencies listed in `requirements.txt` using `pip` inside your favorite virtual environment.

```bash
pip install -r requirements.txt
```


### 💪 Pre-process Kindle clippings
If you are starting with a Kindle export of your highlights (typically called `"My Clippings.txt"`), `re:kindle` can help you pre-process these clippings and separate them by book title.

If you already have a clippings file for a specific book (e.g., `book_clippings.txt` or `book_clippings.html`), you can skip this step.

* Locate your `"My Clippings.txt"` exported from Kindle
* Pre-process the existing clippings and separate them by book title

```bash
> python clip_utils.py --raw_clippings_path "path/to/your/My Clippings.txt" --clippings_library_dir "path/to/your/clippings/library"
```

If you do not specify a `--clippings_library_dir`, the script will use the default directory `CLIPPINGS_DIR` defined in `config.py` (typically `assets/clippings`).

### 🧘 Flexible EPUB selection
`re:kindle` allows you to select the source EPUB from several options (in descending order of priority):
- A specific EPUB file using `--ebook_path "path/to/your/book.epub"`
- A directory containing multiple EPUB files using `--ebook_library_dir "path/to/your/epub/library"`
- The default [Calibre](https://calibre-ebook.com/) library using `--use_calibre_library`  
    - Assumes the Calibre library is located under `$USER_HOME/Calibre Library`

The last two options will display an interactive command-line menu to select the desired EPUB file.

```
💽 Available source EPUBs under '$USER_HOME/Calibre Library':
- [0] Dostoyevsky - Notes from Underground.epub
- [1] Isherwood - A Single Man.epub
- [2] Vargas Llosa - The Feast of the Goat.epub

Select your source EPUB: _
```

###  Flexible clippings selection and formats
Similar to the EPUB selection, you can choose the source clippings file from several options (in descending order of priority):
- A specific clippings file using `--clippings_path "path/to/your/clippings.txt"`
- A directory containing multiple clippings files using `--clippings_library_dir "path/to/your/clippings/library"`
- The default clippings directory (if none of the above are provided)
    - Assumes the clippings directory is located under `assets/clippings` (see `CLIPPINGS_DIR` in `config.py`)

The last two options will display an interactive command-line menu to select the desired clippings file.

```
💽 Available clippings in 'assets/clippings' matching EPUB name:
- [0] Dostoyevsky - Notes from Underground.txt
- [1] Isherwood - A Single Man.html
- [2] Vargas Llosa - The Feast of the Goat.txt
- [3] Vargas Llosa - The Feast of the Goat.html

Select your clippings file (default is 0): _
```

**🧠 Smart title matching**

If you want to list only relevant clippings files based on the EPUB title, use the `--smart_title_matching` flag. This will filter the clippings files to those that closely match the title of the selected EPUB.

```bash
> python re_kindle.py [YOUR_EPUB_FLAGS_HERE] --smart_title_matching
```

```
💽 Available clippings in 'assets/clippings' matching EPUB name:
- [0] Vargas Llosa - The Feast of the Goat.txt
- [1] Vargas Llosa - The Feast of the Goat.html

Select your clippings file (default is 0): _
```

**Preview number of highlights and notes**

The flag `--pre_fetch_clippings` allows you to preview the number of highlights and notes in the selected clippings file before proceeding with the re-integration. This is useful to ensure you are working with the correct clippings file.

```bash
> python re_kindle.py [YOUR_EPUB_FLAGS_HERE] --smart_title_matching --pre_fetch_clippings
```

```
💽 Available clippings in 'assets/clippings' matching EPUB name:
- [0] Vargas Llosa - The Feast of the Goat.html [52 highlights/notes]
- [1] Vargas Llosa - The Feast of the Goat.txt [49 highlights/notes]

Select your clippings file (default is 0): _
```
### 💅 Styling your highlights

You can customize the appearance of your highlights in the EPUB by specifying a highlight
color using the `--highlight_color` flag. By default, the highlight color is set to 
yellow (`#fff7aeea`). The available colors are listed in `config.py` under `KNOWN_COLORS`.
You can also specify a custom hex color code (e.g., `--highlight_color "#e6ad28f4"`). 
Visit [color-hex.com](https://www.color-hex.com/) for help choosing a hex color code. 


## Known Issues/TODOs

**1. Footnote included in highlighted text**

When a highlight includes a footnote number and this has been rendered in plain-text 
Kindle export, the highlight is not properly located. 

For example, if the highlight is:

| This is a highlight with a footnote.<sup>1</sup>

Kindle exports it as:

| This is a highlight with a footnote.1

**2. Preserve footnote color**

For HTML exports, user-selected footnote colors could be preserved. This is not currently implemented. At the moment, all footnotes are rendered in yellow. 


## Code formatting

This project uses `uv` to manage the Python environment and dependencies. To set up the project, follow these steps:
```bash
# Install uv, select Python 3.12 and create a virtual environment
brew install uv
uv python install 3.12
uv venv --python 3.12.9
uv init
uv sync
```

`re:kindle` uses `ruff` for code formatting and linting. If you are contributing to the 
project, please use the following command format the code and fix any issues:
```bash
uvx ruff check . --extend-select I --fix; uvx ruff format . --line-length=120
```

## License
Licensed under the Apache License 2.0. See  [LICENSE](LICENSE) for details.
