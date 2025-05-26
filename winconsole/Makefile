all: format winconsole.exe

.PRECIOUS: %.S %.o %.exe

%.o : %.c
	gcc -c $^ -o $@ -fno-unwind-tables -fno-asynchronous-unwind-tables -fno-ident -Os -flto

%.exe : %.o
	gcc $^ -o $@ -lkernel32 -Os -flto -s

format:
	clang-format -i winconsole.c --style=microsoft
