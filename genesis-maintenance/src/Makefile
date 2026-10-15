CC       ?= cc
CPPFLAGS += -DMERC -Dunix -DMEMWATCH
CFLAGS   ?= -O2
CFLAGS   += -std=gnu89 -Wall -Wno-builtin-declaration-mismatch
LDLIBS   ?= -lcrypt

OBJECTS = act_comm.o act_info.o act_move.o act_obj.o act_wiz.o bit.o board.o \
	clan.o clearclass.o comm.o const.o core.o db.o disc.o dragon.o \
	drow.o elemental.o fight.o flag.o handler.o highland.o interp.o \
	kav_info.o kav_wiz.o mage.o magic.o memwatch.o monk.o more.o ninja.o \
	olc.o random.o rename.o rot_wiz.o save.o signals.o sorcerer.o \
special.o stance.o string.o trap.o update.o werewolf.o wizutil.o reconstructed.o \
	wwauspice.o wwbreed.o wwtribe.o

.PHONY: all clean

all: merc

merc: $(OBJECTS)
	$(CC) $(LDFLAGS) -o $@ $(OBJECTS) $(LDLIBS)

%.o: %.c merc.h board.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJECTS) merc
