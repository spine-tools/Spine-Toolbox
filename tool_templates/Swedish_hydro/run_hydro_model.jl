using SpineModel
using SpineData
using JuMP, Clp
using PyCall

# SpineData
pkg = datapackage(@__DIR__, with_data=true)
sdo = Spine_object(pkg)
update_all_datatypes!(sdo)

# SpineModel
jfo = JuMP_object(sdo)
@JuMPout(jfo, Plants, river, downstream, Pmax, Qmin, Mmax, FlowTimeQ, FlowTimeS, Qavg, Smin)
@JuMPout_suffix(jfo, _base, Qmax)
@JuMPout(jfo, M0, Mend, V, constraint_station)
@JuMPout(jfo, p, SpotPrice7D1S) # Expected spot price for one week

solver = ClpSolver()
m = Model(solver=solver) # model with specified solver
river0 = "Skellefteälven"
rho0 = 5 # Penalty on changes in power
scale_inflow = 1.

# filter out Plants that are not in our river
filter!(x -> river[x] == river0, Plants)

Smax = Dict(i => 1000 for i in Plants) # Maximum spillage Smax[i]
rho = Dict(i => rho0 for i in Plants) # Penalty

# Calculate production equivalent
Qmax = Dict() # Maximum discharge Qmax[i,j]
mu = Dict() # Production equivalent mu[i,j]
for i in Plants
    Qmax[i,1] = 0.75*Qmax_base[i]
    Qmax[i,2] = 0.25*Qmax_base[i]
    mu[i,1] = Pmax[i] / (Qmax[i,1] + 0.95*Qmax[i,2]);
    mu[i,2] = 0.95*mu[i,1]; # 5% lower efficiency above 75% discharge
end

# Upstream power plant matrix (assume same spillway as discharge)
Aq = Dict()
for i in Plants
    for j in Plants
        if downstream[j] == i
            Aq[i,j] = 1
        else
            Aq[i,j] = 0
        end
    end
end

# Downstream power plants matrix (including itself)
Ad = Dict((i,j) => 0 for i in Plants, j in Plants if i != j)
merge!(Ad, Dict((i,j) => 1 for i in Plants, j in Plants if i == j))
for i in Plants 
    next = downstream[i]
    while next != "0"
        Ad[i,next] = 1
        next = downstream[next]
    end
end

station_constraint = Dict(v => k for (k,v) in constraint_station)
M0 = Dict(i => M0[station_constraint[i]] * Mmax[i] for i in Plants) # Initial reservoir content M0[i]
Mend = Dict(i => Mend[station_constraint[i]] * Mmax[i] for i in Plants) # Final reservoir content Mend[i]
V = Dict(i => V[station_constraint[i]] * scale_inflow for i in Plants) # Local inflow V[i]

# Flow times
fqH = Dict(i => Int(floor(FlowTimeQ[i]/60)) for i in Plants) # Flow(discharge) time to the nearest dam in whole hours
fqM = Dict(i => Int(mod(FlowTimeQ[i],60)) for i in Plants) # Flow(discharge) time to the nearest dam in remaining minutes
fsH = Dict(i => Int(floor(FlowTimeS[i]/60)) for i in Plants) # Flow(spill) time to the nearest dam in whole hours
fsM = Dict(i => Int(mod(FlowTimeS[i],60)) for i in Plants) # Flow(spill) time to the nearest dam in remaining minutes

T = maximum(SpotPrice7D1S) # Number of hours
# Set up model
@variables m begin
    Q[i in Plants,j=1:2,t in SpotPrice7D1S], (lowerbound=0, upperbound=Qmax[i,j]) # Discharge (total min set in constraints)
    S[i in Plants,t in SpotPrice7D1S], (lowerbound=Smin[i], upperbound=Smax[i]) # Spillage
    M[i in Plants,t in SpotPrice7D1S], (lowerbound=0, upperbound=Mmax[i]) # Reservoir level
    P[t in SpotPrice7D1S] # Total power generation
    SflowT[i in Plants,t in SpotPrice7D1S] # Spill reaching station i at time t
    QflowT[i in Plants,t in SpotPrice7D1S] # Flow reaching station i at time t
    Dp[i in Plants,t in SpotPrice7D1S], (lowerbound=0) # Penalty on positive flow derivative
    Dm[i in Plants,t in SpotPrice7D1S], (lowerbound=0) # Penalty on negative flow derivative
    Qtot[i in Plants,t in SpotPrice7D1S] # Total discharge in station
end

# Objective function: maximize total profit minus penalty for changes
@objective(m, Max, sum(p[t]*P[t] for t in SpotPrice7D1S)
    - sum(rho[i]*(Dp[i,t]+Dm[i,t]) for i in Plants,t in SpotPrice7D1S))

# Constraints (constraint name, equation)
@constraints m begin
    Pwr[t in SpotPrice7D1S], P[t] == sum(mu[i,j]*Q[i,j,t] for i in Plants, j=1:2) # Power generation
    EndRes[i in Plants],  M[i,T] == Mend[i] # End reservoir level
    HydBal[i in Plants,t in SpotPrice7D1S], M[i,t] == (t==1 ? M0[i] :  M[i,t-1]) + V[i] - # Hydrobalance
        Qtot[i,t] - S[i,t] + sum(Aq[i,ii]*(QflowT[ii,t]+SflowT[ii,t]) for ii in Plants) +
        sum((t <= fqH[ii] ? Qavg[ii]*Aq[i,ii]  : 0) for ii in Plants) + # Ersätt med värde beräknat från V?
        sum((t == fqH[ii] + 1 ? Qavg[ii]*Aq[i,ii]*(60-fqM[ii])/60 : 0) for ii in Plants)
    QflowTime[i in Plants,t in SpotPrice7D1S], QflowT[i,t] == fqM[i]/60 * (t-fqH[i]-1>0 ? Qtot[i,t-fqH[i]-1] : 0) +
        (60-fqM[i])/60 * (t-fqH[i]>0 ? Qtot[i,t-fqH[i]] : 0) # Total flow with delay
    SflowTime[i in Plants,t in SpotPrice7D1S], SflowT[i,t] == fsM[i]/60 * (t-fsH[i]-1>0 ? S[i,t-fsH[i]-1] : 0) +
        (60-fsM[i])/60 * (t-fsH[i]>0 ? S[i,t-fsH[i]] : 0) # Total spill with delay
    Qlow[i in Plants,t in SpotPrice7D1S], Qtot[i,t] >= Qmin[i] # Lower bound on total plant discharge
    Qprim[i in Plants,t in SpotPrice7D1S], Qtot[i,t] - (t>1 ? Qtot[i,t-1] : 0) == Dp[i,t] - Dm[i,t] # Derivative of discharge
    Qsum[i in Plants,t in SpotPrice7D1S], Qtot[i,t] == sum(Q[i,:,t]) # Sum for export
end

solution = solve(m)

# Get values from Jump variables
for s in ["M","S","Q","Qtot","P","SflowT","QflowT","Dp"]
    s = Symbol(s)
    @eval($s = getvalue($s))
end
revenue = getobjectivevalue(m)


plt = pyimport_conda("matplotlib.pyplot", "matplotlib")
plt[:plot]([P[t] for t in SpotPrice7D1S])
plt[:ylabel]("Total power generation (MW)")
plt[:xlabel]("Time (hour)")
plt[:show]()




# objects of class "Plants" where the "river" is "Skellefteälven"
#objects = filter(x -> x[:Object_class] == "Plants" && parameter_value(sdo, x[:Object], "river") == river, sdo.objects)
# append objects from other classes
#append!(objects, filter(x -> x[:Object_class] != "Plants", sdo.objects))
