-- Author: PROJECT TITAN
-- Name: PROJECT TITAN Live Bridge
-- Namespace: global
-- Description: Bidirectional local MCP bridge for GIANTS Editor selection and transforms
-- Hide: no
-- AlwaysLoaded: yes

local bridgeDirectory = getAppDataPath() .. "project-titan-bridge"
if not fileExists(bridgeDirectory) then
    createFolder(bridgeDirectory)
end

local requestPath = bridgeDirectory .. "/request.xml"

ProjectTitanEditorBridge = ProjectTitanEditorBridge or {}
local bridge = ProjectTitanEditorBridge

if bridge.updateListener ~= nil then
    pcall(removeUpdateListener, bridge.updateListener)
    bridge.updateListener = nil
end

bridge.sessionId = string.gsub(tostring({}), "[^%w]", "")
bridge.lastRequestId = nil
bridge.elapsedMs = 0
bridge.pollIntervalMs = 100
bridge.maxSelection = 200

local function normalizePath(path)
    if path == nil then
        return ""
    end
    local normalized = string.gsub(path, "\\", "/")
    normalized = string.lower(normalized)
    normalized = string.gsub(normalized, "/+$", "")
    return normalized
end

local function readVector(xmlFile, key)
    local value = getXMLString(xmlFile, key)
    if value == nil then
        return nil
    end

    local result = {}
    for component in string.gmatch(value, "[^,%s]+") do
        local number = tonumber(component)
        if number == nil or number ~= number or math.abs(number) > 1000000 then
            error("Invalid " .. key .. " vector")
        end
        table.insert(result, number)
    end

    if #result ~= 3 then
        error("Invalid " .. key .. " vector")
    end
    return result
end

local function formatVector(x, y, z)
    return string.format("%.9g %.9g %.9g", x, y, z)
end

local function collectSelection()
    local selectedCount = getNumSelected() or 0
    local exportedCount = math.min(selectedCount, bridge.maxSelection)
    local nodes = {}

    for index = 0, exportedCount - 1 do
        local node = getSelection(index)
        if node ~= nil and node ~= 0 then
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
            table.insert(nodes, {
                runtimeId = node,
                name = getName(node) or "",
                parentRuntimeId = parent,
                parentName = parentName,
                localTranslation = formatVector(tx, ty, tz),
                worldTranslation = formatVector(wx, wy, wz),
                rotation = formatVector(rx, ry, rz),
                scale = formatVector(sx, sy, sz),
                childCount = getNumOfChildren(node) or 0,
            })
        end
    end

    return selectedCount, nodes
end

local function writeResponse(requestId, success, errorMessage, modifiedCount)
    local responsePath = bridgeDirectory .. "/response-" .. requestId .. ".xml"
    local xmlFile = createXMLFile("projectTitanEditorBridgeResponse", responsePath, "response")
    if xmlFile == 0 then
        print("PROJECT TITAN: could not create bridge response at " .. responsePath)
        return false
    end

    local sceneFilename = getSceneFilename() or ""
    local rootNode = getRootNode()
    local rootName = ""
    if rootNode ~= nil and rootNode ~= 0 then
        rootName = getName(rootNode) or ""
    end

    local selectedCount, nodes = collectSelection()
    setXMLString(xmlFile, "response#id", requestId)
    setXMLString(xmlFile, "response#sessionId", bridge.sessionId)
    setXMLInt(xmlFile, "response#success", success and 1 or 0)
    setXMLString(xmlFile, "response#sceneFilename", sceneFilename)
    setXMLString(xmlFile, "response#sceneRootName", rootName)
    setXMLInt(xmlFile, "response#selectedCount", selectedCount)
    setXMLInt(xmlFile, "response#selectionTruncated", selectedCount > bridge.maxSelection and 1 or 0)
    setXMLInt(xmlFile, "response#modifiedCount", modifiedCount or 0)
    if errorMessage ~= nil and errorMessage ~= "" then
        setXMLString(xmlFile, "response#error", errorMessage)
    end

    for index, node in ipairs(nodes) do
        local key = string.format("response.node(%d)", index - 1)
        setXMLInt(xmlFile, key .. "#runtimeId", node.runtimeId)
        setXMLString(xmlFile, key .. "#name", node.name)
        setXMLInt(xmlFile, key .. "#parentRuntimeId", node.parentRuntimeId)
        setXMLString(xmlFile, key .. "#parentName", node.parentName)
        setXMLString(xmlFile, key .. "#localTranslation", node.localTranslation)
        setXMLString(xmlFile, key .. "#worldTranslation", node.worldTranslation)
        setXMLString(xmlFile, key .. "#rotation", node.rotation)
        setXMLString(xmlFile, key .. "#scale", node.scale)
        setXMLInt(xmlFile, key .. "#childCount", node.childCount)
    end

    local saved = saveXMLFile(xmlFile)
    delete(xmlFile)
    if not saved then
        print("PROJECT TITAN: failed to write bridge response at " .. responsePath)
    end
    return saved
end

local function setSelectedTransform(xmlFile, sceneFilename)
    local expectedSceneFilename = getXMLString(xmlFile, "request#expectedSceneFilename") or ""
    if normalizePath(sceneFilename) ~= normalizePath(expectedSceneFilename) then
        error("The active Editor scene changed before the transform was applied")
    end

    local translation = readVector(xmlFile, "request.translation#value")
    local rotation = readVector(xmlFile, "request.rotation#value")
    local scale = readVector(xmlFile, "request.scale#value")
    if translation == nil and rotation == nil and scale == nil then
        error("No transform values were supplied")
    end

    local selectedCount = getNumSelected() or 0
    local expectedCount = getXMLInt(xmlFile, "request.selection#count") or 0
    if expectedCount < 1 or expectedCount > bridge.maxSelection or selectedCount ~= expectedCount then
        error("The Editor selection changed; read it again before applying a transform")
    end

    local selectedNodes = {}
    for index = 0, selectedCount - 1 do
        local selectedNode = getSelection(index)
        local expectedRuntimeId = getXMLInt(
            xmlFile,
            string.format("request.selection.node(%d)#runtimeId", index)
        )
        if selectedNode == nil or selectedNode == 0 or selectedNode ~= expectedRuntimeId then
            error("The Editor selection changed; read it again before applying a transform")
        end
        table.insert(selectedNodes, selectedNode)
    end

    for _, node in ipairs(selectedNodes) do
        if translation ~= nil then
            setTranslation(node, translation[1], translation[2], translation[3])
        end
        if rotation ~= nil then
            setRotation(node, rotation[1], rotation[2], rotation[3])
        end
        if scale ~= nil then
            setScale(node, scale[1], scale[2], scale[3])
        end
    end

    return #selectedNodes
end

local function selectNodeByNamePath(xmlFile, sceneFilename)
    local expectedSceneFilename = getXMLString(xmlFile, "request#expectedSceneFilename") or ""
    if normalizePath(sceneFilename) ~= normalizePath(expectedSceneFilename) then
        error("The active Editor scene changed before the node was selected")
    end

    local pathCount = getXMLInt(xmlFile, "request.namePath#count") or 0
    if pathCount < 1 or pathCount > 256 then
        error("Invalid I3D node path")
    end

    local names = {}
    for index = 0, pathCount - 1 do
        local name = getXMLString(xmlFile, string.format("request.namePath.part(%d)#name", index))
        if name == nil then
            error("Invalid I3D node path")
        end
        table.insert(names, name)
    end

    local currentNode = getRootNode()
    if currentNode == nil or currentNode == 0 then
        error("No I3D scene is open in GIANTS Editor")
    end

    local firstPathIndex = 1
    if names[1] == (getName(currentNode) or "") then
        firstPathIndex = 2
    end

    for index = firstPathIndex, #names do
        local matchingChild = 0
        local matchingCount = 0
        local childCount = getNumOfChildren(currentNode) or 0
        for childIndex = 0, childCount - 1 do
            local child = getChildAt(currentNode, childIndex)
            if child ~= nil and child ~= 0 and (getName(child) or "") == names[index] then
                matchingChild = child
                matchingCount = matchingCount + 1
            end
        end

        if matchingCount == 0 then
            error("The I3D node path was not found in the open Editor scene")
        end
        if matchingCount > 1 then
            error("The I3D node path is ambiguous because a parent has duplicate child names")
        end
        currentNode = matchingChild
    end

    clearSelection()
    addSelection(currentNode)
    if getNumSelected() ~= 1 or getSelection(0) ~= currentNode then
        error("GIANTS Editor did not select the requested node")
    end

    return 0
end

function bridge.processRequest()
    if not fileExists(requestPath) then
        return
    end

    local xmlFile = loadXMLFile("projectTitanEditorBridgeRequest", requestPath)
    if xmlFile == nil or xmlFile == 0 then
        return
    end

    local requestId = getXMLString(xmlFile, "request#id") or ""
    if requestId == "" or string.match(requestId, "^[%w%-]+$") == nil then
        delete(xmlFile)
        return
    end
    if requestId == bridge.lastRequestId then
        delete(xmlFile)
        return
    end
    bridge.lastRequestId = requestId

    local operation = getXMLString(xmlFile, "request#operation") or ""
    local requestSessionId = getXMLString(xmlFile, "request#sessionId") or ""
    local sceneFilename = getSceneFilename() or ""
    local success, result = pcall(function()
        if operation == "hello" then
            return 0
        end

        if requestSessionId ~= bridge.sessionId then
            error("The Editor bridge session changed; retry the request")
        end

        if operation == "status" or operation == "selection" then
            return 0
        end

        if operation == "setTransform" then
            return setSelectedTransform(xmlFile, sceneFilename)
        end

        if operation == "selectNode" then
            return selectNodeByNamePath(xmlFile, sceneFilename)
        end

        error("Unsupported Editor bridge operation: " .. operation)
    end)

    delete(xmlFile)
    local errorMessage = nil
    if not success then
        errorMessage = tostring(result)
    end
    writeResponse(requestId, success, errorMessage, success and result or 0)
end

function bridge.onUpdate(_self, dt)
    bridge.elapsedMs = bridge.elapsedMs + (dt or 0)
    if bridge.elapsedMs < bridge.pollIntervalMs then
        return
    end

    bridge.elapsedMs = 0
    bridge.processRequest()
end

bridge.updateListener = addUpdateListener(
    "ProjectTitanEditorBridge_update",
    bridge,
    bridge.onUpdate
)

print("PROJECT TITAN: live Editor bridge is running.")

