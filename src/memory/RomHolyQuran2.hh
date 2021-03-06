#ifndef ROMHOLYQURAN2_HH
#define ROMHOLYQURAN2_HH

#include "MSXRom.hh"
#include "RomBlockDebuggable.hh"

namespace openmsx {

class RomHolyQuran2 : public MSXRom
{
public:
	RomHolyQuran2(const DeviceConfig& config, Rom&& rom);

	void reset(EmuTime::param time) override;
	byte readMem(word address, EmuTime::param time) override;
	byte peekMem(word address, EmuTime::param time) const override;
	void writeMem(word address, byte value, EmuTime::param time) override;
	const byte* getReadCacheLine(word address) const override;
	byte* getWriteCacheLine(word address) const override;

	template<typename Archive>
	void serialize(Archive& ar, unsigned version);

private:
	struct Blocks final : RomBlockDebuggableBase {
		explicit Blocks(RomHolyQuran2& device);
		byte read(unsigned address) override;
	} romBlocks;

	const byte* bank[4];
	bool decrypt;
};

} // namespace openmsx

#endif
