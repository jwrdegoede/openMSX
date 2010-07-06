// $Id$

#ifndef XMLELEMENT_HH
#define XMLELEMENT_HH

#include "serialize_constr.hh"
#include <map>
#include <string>
#include <vector>
#include <memory>

namespace openmsx {

class FileContext;

class XMLElement
{
public:
	//
	// Basic functions
	//

	// construction, destruction, copy, assign
	explicit XMLElement(const std::string& name,
	                    const std::string& data = "");
	XMLElement(const XMLElement& element);
	const XMLElement& operator=(const XMLElement& element);
	~XMLElement();

	// name
	const std::string& getName() const { return name; }
	void setName(const std::string& name);

	// data
	const std::string& getData() const { return data; }
	void setData(const std::string& data);

	// attribute
	typedef std::map<std::string, std::string> Attributes;
	void addAttribute(const std::string& name, const std::string& value);
	void setAttribute(const std::string& name, const std::string& value);
	const Attributes& getAttributes() const;

	// parent
	XMLElement* getParent();
	const XMLElement* getParent() const;

	// child
	typedef std::vector<XMLElement*> Children;
	void addChild(std::auto_ptr<XMLElement> child);
	std::auto_ptr<XMLElement> removeChild(const XMLElement& child);
	const Children& getChildren() const { return children; }

	// filecontext
	void setFileContext(std::auto_ptr<FileContext> context);
	FileContext& getFileContext() const;

	//
	// Convenience functions
	//

	// data
	bool getDataAsBool() const;
	int getDataAsInt() const;
	double getDataAsDouble() const;

	// attribute
	bool hasAttribute(const std::string& name) const;
	const std::string& getAttribute(const std::string& attName) const;
	const std::string getAttribute(const std::string& attName,
	                          const std::string defaultValue) const;
	bool getAttributeAsBool(const std::string& attName,
	                        bool defaultValue = false) const;
	int getAttributeAsInt(const std::string& attName,
	                      int defaultValue = 0) const;
	const std::string& getId() const;

	// child
	const XMLElement* findChild(const std::string& name) const;
	XMLElement* findChild(const std::string& name);
	const XMLElement& getChild(const std::string& name) const;
	const XMLElement* findChildWithAttribute(
		const std::string& name, const std::string& attName,
		const std::string& attValue) const;
	XMLElement* findChildWithAttribute(
		const std::string& name, const std::string& attName,
		const std::string& attValue);
	const XMLElement* findNextChild(const std::string& name,
	                                unsigned& fromIndex) const;

	XMLElement& getChild(const std::string& name);
	void getChildren(const std::string& name, Children& result) const;

	XMLElement& getCreateChild(const std::string& name,
	                           const std::string& defaultValue = "");
	XMLElement& getCreateChildWithAttribute(
		const std::string& name, const std::string& attName,
		const std::string& attValue, const std::string& defaultValue = "");

	const std::string& getChildData(const std::string& name) const;
	std::string getChildData(const std::string& name,
	                         const std::string& defaultValue) const;
	bool getChildDataAsBool(const std::string& name,
	                        bool defaultValue = false) const;
	int getChildDataAsInt(const std::string& name,
	                      int defaultValue = 0) const;
	void setChildData(const std::string& name, const std::string& value);

	void removeAllChildren();

	// various
	std::string dump() const;
	static std::string XMLEscape(const std::string& str);

	template<typename Archive>
	void serialize(Archive& ar, unsigned version);

private:
	void dump(std::string& result, unsigned indentNum) const;

	std::string name;
	std::string data;
	Children children;
	Attributes attributes;
	XMLElement* parent;
	std::auto_ptr<FileContext> context;
};

template<> struct SerializeConstructorArgs<XMLElement>
{
	typedef Tuple<std::string, std::string> type;
	template<typename Archive> void save(Archive& ar, const XMLElement& xml)
	{
		ar.serialize("name", xml.getName());
		ar.serialize("data", xml.getData());
	}
	template<typename Archive> type load(Archive& ar, unsigned /*version*/)
	{
		std::string name, data;
		ar.serialize("name", name);
		ar.serialize("data", data);
		return make_tuple(name, data);
	}
};

} // namespace openmsx

#endif
