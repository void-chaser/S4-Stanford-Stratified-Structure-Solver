-- Two-layer bare interface through the Lua frontend, normalised the same way
-- as the Python side (R and T as ratios to the incident power).
--
-- The Lua `GetPoyntingFlux(layer, z)` returns the net signed flux, so reflection
-- is the negated backward component.  Printing R and T rather than raw fluxes
-- is what makes the two frontends comparable.

local function sweep(n2)
  S = S4.NewSimulation()
  S:SetLattice({1,0}, {0,1})
  S:SetNumG(1)
  S:AddMaterial("Above", {1,0})
  S:AddMaterial("Below", {n2*n2,0})
  S:AddLayer('Above', 0, 'Above')
  S:AddLayer('Below', 0, 'Below')
  S:SetFrequency(1)
  S:SetExcitationPlanewave({0,0}, {1,0}, {0,0})
  local inc, back = S:GetPoyntingFlux('Above', 0)
  local fwd       = S:GetPoyntingFlux('Below', 0)
  -- The first column is the exit index n2. It used to be the literal 1.0, which
  -- made the row self-inconsistent and left a reader unable to tell which index
  -- the R and T belonged to.
  io.write(string.format("%.12g\t%.12g\t%.12g\n", n2, -back/inc, fwd/inc))
end

sweep(2.0)
