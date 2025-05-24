all: format winconsole.exe

.PRECIOUS: %.S %.o %.exe

%.o : %.c
	gcc -c $^ -o $@ -Os -fno-unwind-tables -fno-asynchronous-unwind-tables -fno-ident

%.exe : %.o
	gcc $^ -o $@ -lmsvcrt -lkernel32 -s

format:
	clang-format -i winconsole.c --style=microsoft
