.PHONY: default all

default: test

CC        := clang
CFLAGS    := -Wall -O1 -g -fsanitize=address -fno-omit-frame-pointer
CFLAGS    += -fcolor-diagnostics

mime.types := output/mime.types
mime.rl    := output/mime.rl
mime.rl.c  := output/mime.rl.c
mime.gperf := output/mime.gperf
mime.gp.c  := output/mime.gp.c
rl_test    := output/rl_test
gp_test    := output/gp_test

LOOPS ?= 999999

$(mime.types):
	mkdir -p $(dir $@)
	wget -qO- https://raw.githubusercontent.com/h5bp/server-configs-nginx/master/mime.types > $@

$(mime.rl) : mime2ragel.py $(mime.types)
	mkdir -p $(dir $@)
	python3 ./mime2ragel.py -ragel $(mime.types) > $@

$(mime.gperf) : mime2ragel.py $(mime.types)
	mkdir -p $(dir $@)
	python3 ./mime2ragel.py -gperf $(mime.types) > $@

$(mime.rl.c) : $(mime.rl)
	mkdir -p $(dir $@)
	ragel -o $@ $<

$(mime.gp.c) : $(mime.gperf)
	mkdir -p $(dir $@)
	gperf --lookup-function-name=get_mime_type -t -G $< > $@

$(rl_test) : $(mime.rl.c)
	mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

$(gp_test) : $(mime.gp.c)
	mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

test: $(rl_test) $(gp_test)
	time ./$(rl_test) $(LOOPS)
	time ./$(gp_test) $(LOOPS)

all:

clean:
	-rm -rf output
