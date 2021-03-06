#ifndef GLTEXTURE_HH
#define GLTEXTURE_HH

#include "BaseImage.hh"
#include "GLUtil.hh"
#include "openmsx.hh"
#include <string>

class SDLSurfacePtr;

namespace openmsx {

class GLImage final : public BaseImage
{
public:
	GLImage(OutputSurface& output, const std::string& filename);
	GLImage(OutputSurface& output, SDLSurfacePtr image);
	GLImage(OutputSurface& output, const std::string& filename, float scaleFactor);
	GLImage(OutputSurface& output, const std::string& filename, gl::ivec2 size);
	GLImage(OutputSurface& output, gl::ivec2 size, unsigned rgba);
	GLImage(OutputSurface& output, gl::ivec2 size, const unsigned* rgba,
	        int borderSize, unsigned borderRGBA);

	void draw(OutputSurface& output, gl::ivec2 pos,
	          uint8_t r, uint8_t g, uint8_t b, uint8_t alpha) override;

private:
	gl::vec2 texCoord;
	gl::Texture texture; // must come after size and texCoord
	int borderSize;
	int bgA[4], borderA;
	uint8_t bgR[4], bgG[4], bgB[4];
	uint8_t borderR, borderG, borderB;
};

} // namespace openmsx

#endif
