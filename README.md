README
======

Alas, there is no epub version of the Jungle World, https://jungle-world.com .

Hence this little Python3 script to download the current issue and its cover
image and then convert it to epub.


Install
=======

	$ virtualenv --python=python3 venv
	$ source venv/bin/activate
	$ git clone https://github.com/kodeaffe/jw2epub
	$ cd jw2epub
	$ pip install -r requirements.txt




Usage
=====

This will download and convert the current issue:

	$ ./jw2epub

If you want to download a specific issue, use this invocation:

	$ ./jw2epub 2017.05

The generated epub file is put into the current directory.


If you want to read the complete current issue or have to make adjustments to
the configuration defaults, copy settings.py.example to settings.py and edit
that file.

Running the script will create a directory of downloaded stories as a
subdirectory of CACHEDIR as specified in settings.py, e.g cache/2017.05/ . It
will also download the cover image there.
