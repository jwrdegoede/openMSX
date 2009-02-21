// $Id$

#include "EmptyDiskPatch.hh"
#include "SectorAccessibleDisk.hh"
#include <cassert>

namespace openmsx {

EmptyDiskPatch::EmptyDiskPatch(SectorAccessibleDisk& disk_)
	: disk(disk_)
{
}

void EmptyDiskPatch::copyBlock(unsigned src, byte* dst, unsigned num) const
{
	(void)num;
	assert(num == SectorAccessibleDisk::SECTOR_SIZE);
	disk.readSectorImpl(src / SectorAccessibleDisk::SECTOR_SIZE, dst);
}

unsigned EmptyDiskPatch::getSize() const
{
	return disk.getNbSectors() * SectorAccessibleDisk::SECTOR_SIZE;
}

void EmptyDiskPatch::getFilenames(std::vector<Filename>& /*result*/) const
{
	// nothing
}

} // namespace openmsx

