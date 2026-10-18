-- e2e_lua_r9m3a.lua -- one Lua-side E2E point step.
-- usage: S4_e2e e2e_lua_r9m3a.lua SPEC PHASE   (SPEC in fft|jones|nv|vl; PHASE in clean|inject|fresh)
local spec = arg[1] or "fft"
local phase = arg[2] or "clean"

local function build()
    local S = S4.NewSimulation()
    S:SetLattice({1,0}, {0,1})
    S:SetNumG(25)
    S:AddMaterial("Air", {1,0})
    S:AddMaterial("Slab", {12,0})
    S:AddLayer("Top", 0, "Air")
    S:AddLayer("Middle", 0.5, "Slab")
    S:SetLayerPatternCircle("Middle", "Air", {0,0}, 0.2)
    S:AddLayerCopy("Bottom", 0, "Top")
    S:SetFrequency(0.4)
    S:SetExcitationPlanewave({0,0}, {1,0}, {0,0})
    if S.UsePolarizationDecomposition then pcall(function() S:UsePolarizationDecomposition() end) end
    if spec == "jones" then
        if S.UseJonesVectorBasis then pcall(function() S:UseJonesVectorBasis() end) end
    elseif spec == "nv" then
        if S.UseNormalVectorBasis then pcall(function() S:UseNormalVectorBasis() end) end
    end
    if S.SetDiscretizedEpsilon then pcall(function() S:SetDiscretizedEpsilon(true) end) end
    return S
end

local S = build()
local f, b = S:GetPoyntingFlux("Bottom", 0)
print(string.format("VALUES %.17g %.17g", f, b))
print("PHASE " .. phase .. " OK")
