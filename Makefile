.SILENT:

all:
	-ln -s lab3b.py lab3b
	chmod +x lab3b

clean:
	rm -rf lab3b *.tar.gz

dist:
	tar -cvzf lab3b-904756085.tar.gz lab3b.py README Makefile