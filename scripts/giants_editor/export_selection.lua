-- PROJECT TITAN: export the current GIANTS Editor selection to XML.
-- Set this to a file inside the same folder configured as TITAN_PROJECT_ROOT.
local outputPath = "C:/REPLACE/WITH/YOUR/PROJECT/.project-titan-editor-selection.xml"
local maxNodes = 500

local selectedCount = getNumSelected()
local exportedCount = math.min(selectedCount, maxNodes)
local xmlFile = createXMLFile("projectTitanSelection", outputPath, "projectTitanSelection")

if xmlFile == 0 then
    print("PROJECT TITAN: could not create selection snapshot at " .. outputPath)
    return
end

setXMLInt(xmlFile, "projectTitanSelection#version", 1)
setXMLInt(xmlFile, "projectTitanSelection#selectedCount", selectedCount)
setXMLInt(xmlFile, "projectTitanSelection#exportedCount", exportedCount)

for index = 0, exportedCount - 1 do
    local node = getSelection(index)
    if node ~= 0 then
        local parent = getParent(node)
        local parentName = ""
        if parent ~= nil and parent ~= 0 then
            parentName = getName(parent) or ""
        else
            parent = 0
        end

        local tx, ty, tz = getTranslation(node)
        local wx, wy, wz = getWorldTranslation(node)
        local rx, ry, rz = getRotation(node)
        local sx, sy, sz = getScale(node)
        local childCount = getNumOfChildren(node)
        local key = string.format("projectTitanSelection.node(%d)", index)

        setXMLInt(xmlFile, key .. "#runtimeId", node)
        setXMLString(xmlFile, key .. "#name", getName(node) or "")
        setXMLInt(xmlFile, key .. "#parentRuntimeId", parent)
        setXMLString(xmlFile, key .. "#parentName", parentName)
        setXMLString(xmlFile, key .. "#localTranslation", string.format("%.6f %.6f %.6f", tx, ty, tz))
        setXMLString(xmlFile, key .. "#worldTranslation", string.format("%.6f %.6f %.6f", wx, wy, wz))
        setXMLString(xmlFile, key .. "#rotation", string.format("%.6f %.6f %.6f", rx, ry, rz))
        setXMLString(xmlFile, key .. "#scale", string.format("%.6f %.6f %.6f", sx, sy, sz))
        setXMLInt(xmlFile, key .. "#childCount", childCount)
    end
end

local saved = saveXMLFile(xmlFile)
delete(xmlFile)

if saved then
    print("PROJECT TITAN: exported " .. exportedCount .. " of " .. selectedCount .. " selected nodes.")
else
    print("PROJECT TITAN: failed to save selection snapshot at " .. outputPath)
end
