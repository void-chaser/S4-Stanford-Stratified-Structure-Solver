-- Mirror of examples/2d/Fan_PRB_65_2002/fig12.lua, normalised.
--
-- The original example prints the raw signed Poynting flux, whose sign
-- convention differs between the Lua and Python frontends.  To make the two
-- frontends comparable this script prints the same three columns as
-- testing/s4test/mirror_fig12.py:
--
--     freq <tab> T <tab> R
--
-- with T and R normalised by the incident power.  Geometry and parameters are
-- otherwise identical to the shipped example.

S = S4.NewSimulation()
S:SetLattice({1,0}, {0,1})
S:SetNumG(100)
S:AddMaterial("Silicon", {12,0})
S:AddMaterial("Vacuum", {1,0})

S:AddLayer('AirAbove', 0, 'Vacuum')
S:AddLayer('Slab', 0.5, 'Silicon')
S:SetLayerPatternCircle('Slab', 'Vacuum', {0,0}, 0.2)
S:AddLayerCopy('AirBelow', 0, 'AirAbove')

S:SetExcitationPlanewave({0,0}, {1,0}, {0,0})

for freq = 0.25, 0.27, 0.003 do
	S:SetFrequency(freq)
	local inc, back = S:GetPoyntingFlux('AirAbove', 0)
	local fwd       = S:GetPoyntingFlux('AirBelow', 0)
	io.write(string.format("%.12g\t%.12g\t%.12g\n", freq, fwd/inc, -back/inc))
	io.stdout:flush()
end
