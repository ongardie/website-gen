This repository contains a static web site generator that is used for
<https://ongardie.net/>. While this code is fairly small, it's a bit peculiar
and not documented well. If you're starting a new project, check out
alternatives like [Hugo](https://gohugo.io/) and
[Jekyll](https://jekyllrb.com/) instead.

# Getting Started

1. Install the dependencies in a Python virtual environment:

    ```sh
    python3 -m venv env
    . env/bin/activate
    pip install -r requirements.txt
    ```

    In the future, you'll need to run just the "activate" line to enable the
    virtual environment.

2. Create a `config.ini` file like this one:

    ```ini
    [controller]
    URL_PREFIX =
    FULL_URL_PREFIX = http://localhost:8000
    AUTHOR = Your Name
    AUTHOR_PAGE = /you
    ```

3. Create a "var" directory with templates and content.

4. Run the static site generator:

    ```sh
    ./main.py --help
    ```

5. Start a web server to view the output (so that the links work):

    ```sh
    python -m http.server --bind localhost 8000 --directory path/to/output
    ```

6. Open <http://localhost:8000/> in your web browser.
