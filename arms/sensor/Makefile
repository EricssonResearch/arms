
build:
	swig -python -py3 tcp.i
	python3.5 setup.py build_ext
	sudo rm -f /usr/lib/libtcp.so
	sudo mv libtcp.so /usr/lib
	sudo chmod 755 /usr/lib/libtcp.so
tcp.o: tcp.c
	gcc -fPIC -c tcp.c
tcp_wrap.o: tcp_wrap.c
	gcc -fPIC -c tcp_wrap.c -I/usr/include/python3.5 -I/usr/local/lib/python3.5/config
libtcp.so:
	gcc -shared tcp.o tcp_wrap.o -o libtcp.so
