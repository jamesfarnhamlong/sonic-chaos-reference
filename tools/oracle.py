"""Execute original ROM subroutines using kosarev/z80. This is not an SMS emulator.

No graphics, audio, interrupts, scheduler or controller polling are simulated.
Callers explicitly supply RAM state. Mapper writes are modelled for ROM slots 1/2.
"""
import z80
from rom import layout, u16

class Oracle:
    RETURN = 0x0100

    def __init__(self, rom):
        self.rom = rom
        self.cpu = z80.Z80Machine()
        self.mem = self.cpu.memory
        self.mem[:0x8000] = rom[:0x8000]
        self.bank(2, 14)
        self.cpu.set_write_callback(self.write_mapper)
        self.cpu.mark_addrs(0, 0xc000, self.cpu.WRITE_MARK)
        self.cpu.mark_addrs(0xfffd, 3, self.cpu.WRITE_MARK)
        self.rom_writes = []
        self.cpu.set_breakpoint(self.RETURN)
        self.cpu.ix = 0xd500
        self.mem[0xc001:0xd000] = bytes(layout(rom))
        # Equivalent 128-block row stride table at a harness-owned RAM address.
        self.word(0xd168, 0xd800)
        for row in range(128):
            self.word(0xd800 + row*2, row*128)
        self.word(0xd16a, -128)
        self.word(0xd2e0, 0x8000)
        self.mem[0xd12b] = 14
        self.mem[0xd500] = 1
        self.mem[0xd501] = self.mem[0xd502] = 5
        self.mem[0xd36c] = 0x81
        self.word(0xd373, 0x0400)
        self.call(0x3686)  # Original side-sensor initializer.

    def bank(self, slot, bank):
        start = slot * 0x4000
        self.mem[start:start+0x4000] = self.rom[(bank & 31)*0x4000:(bank & 31)*0x4000+0x4000]

    def write_mapper(self, address, value):
        if address < 0xc000:
            self.rom_writes.append((address, value))
            return
        self.mem[address] = value
        if address == 0xffff:
            self.bank(2, value)
        elif address == 0xfffe:
            self.bank(1, value)
        else:
            raise RuntimeError('Unexpected fixed-bank mapper write')

    def word(self, address, value=None):
        if value is None:
            return u16(self.mem, address)
        self.mem[address:address+2] = (value & 65535).to_bytes(2, 'little')

    def position(self, x, y):
        self.word(0xd511, x); self.word(0xd514, y)

    def call(self, address, bc=0, de=0):
        self.cpu.pc = address
        self.cpu.bc = bc & 65535
        self.cpu.de = de & 65535
        self.cpu.sp = 0xdfe0
        self.word(self.cpu.sp, self.RETURN)
        # run() may yield at an emulated frame boundary. Limit total work.
        for _ in range(20):
            self.cpu.ticks_to_stop = 100000
            self.cpu.run()
            if self.cpu.pc == self.RETURN:
                return
        raise RuntimeError(f'Call ${address:04X} failed to return; PC=${self.cpu.pc:04X}')

    def collision_sample(self, x, y, dx=0, dy=0, plane=0):
        self.position(x, y)
        self.mem[0xd525] = plane
        self.call(0x7666, dx, dy)
        return dict(tile=self.mem[0xd353], map_address=self.word(0xd354),
                    x=self.word(0xd358), y=self.word(0xd35a),
                    flags=self.mem[0xd364], modifier=self.mem[0xd100],
                    vertical=self.mem[0xd368], horizontal=self.mem[0xd367])
