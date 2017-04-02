# Jungle World 2 EPUB

There is currently no official epub version of the [Jungle World](https://jungle.world).

Hence this little Python3 script to download the current issue and its cover
image and then convert it to epub.

### NOTE

This version supports only the new version of the website as of March 2017.
The old version is supported up to git tag `pre201703`.



## Install

	$ virtualenv --python=python3 venv
	$ source venv/bin/activate
	$ git clone https://github.com/kodeaffe/jw2epub
	$ cd jw2epub
	$ pip install -r requirements.txt



## Usage

This will download and convert the current issue:

	$ ./jw2epub.py

If you want to download a specific issue, use this invocation:

	$ ./jw2epub.py 2017/12

The generated epub file is put into the current directory.


If you want to read the complete current issue or have to make adjustments to
the configuration defaults, copy settings.py.example to settings.py and edit
that file.

Running the script will create a directory of downloaded stories as a
subdirectory of CACHEDIR as specified in settings.py, e.g cache/2017/12/ . It
will also download the cover image there.



# Documentation

If you want to generate documentation, you need to install sphinx and run make:

	$ pip install Sphinx
	$ cd docs/ && make html

Entry point for the generated documentation is at `docs/_build/html/index.html`
