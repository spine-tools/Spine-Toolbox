using SpineModel
using SpineData
using JuMP, Clp

path = "/home/manuelma/Codes/spine/toolbox/tool_templates/Swedish_hydro/input"
#pkg_desc = infer(path)
#
#set_primary_key!(pkg_desc, "Plants", ["station_index"])
#
#add_foreign_key!(pkg_desc, "Plants", ["downstream"], "Plants", ["station_index"])
#add_foreign_key!(pkg_desc, "Constraints", ["constraint_station"], "Plants", ["station_name"])
#
#save_datapackage(pkg_desc, path)

sdo = build_Spine_object(joinpath(path, "datapackage.json"))
update_all_datatypes!(sdo)

jfo = build_JuMP_object(sdo)

solver = ClpSolver()
current_river = "Skellefteälven"
rho = 5 # Penalty on changes in power
scale_inflow = 1.

@unpack(jfo, Plants, river, downstream, Pmax, Qmax, Qmin, Mmax, FlowTimeQ, FlowTimeS, Qavg, Smin)

station_index = filter(x -> river[x] == current_river, Plants)
downstream = [downstream[i] for i in station_index]
Pmax = [Pmax[i] for i in station_index]
Qmax = [Qmax[i] for i in station_index]
Qmin = [Qmin[i] for i in station_index]
Mmax = [Mmax[i] for i in station_index]
FlowTimeQ = [FlowTimeQ[i] for i in station_index]
FlowTimeS = [FlowTimeS[i] for i in station_index]
Smin = [Smin[i] for i in station_index]
Qavg = [Qavg[i] for i in station_index]
N = length(station_index) # Number of reservoirs
Smax = 1000*ones(N) # Maximum spillage Smax[i]
rho = ones(N) * rho # Penalty

# Calculate production equivalent
Qmax = [0.75*Qmax 0.25*Qmax] # Maximum discharge Qmax[i,j]
mu = zeros(Qmax) # Production equivalent mu[i,j]
for i = 1:N
   mu[i,1] = Pmax[i] / (Qmax[i,1] + 0.95*Qmax[i,2]);
   mu[i,2] = 0.95*mu[i,1]; # 5% lower efficiency above 75% discharge
end

# Upstream power plant matrix (assume same spillway as discharge)
Aq = zeros(Int8, N, N);
for i = 1:N
    for j = 1:N
        if downstream[j] == station_index[i]
           Aq[i,j] = 1
        end
    end
end

# Downstream power plants matrix (including itself)
Ad = eye(Int16,N)
for i = 1:N-1
    col = i
    while true
       ind = find(Aq[:,col])
       if length(ind)==1
           Ad[i,ind] = 1
           col = ind
       else
           break
       end
    end
end

# Load M0, Mend and V
@unpack(jfo, M0, Mend, V, constraint_station)
station_constraint = Dict(v => k for (k,v) in constraint_station)

M0 = [M0[station_constraint[i]] for i in station_index] .* Mmax # Initial reservoir content M0[i]
Mend = [Mend[station_constraint[i]] for i in station_index] .* Mmax # Final reservoir content Mend[i]
V = [V[station_constraint[i]] for i in station_index] * scale_inflow # Local inflow V[i]

# Flow times
fqH = Int.(floor.(FlowTimeQ/60)) # Flow(discharge) time to the nearest dam in whole hours
fqM = Int.(mod.(FlowTimeQ,60)) # Flow(discharge) time to the nearest dam in remaining minutes
fsH = Int.(floor.(FlowTimeS/60)) # Flow(spill) time to the nearest dam in whole hours
fsM = Int.(mod.(FlowTimeS,60)) # Flow(spill) time to the nearest dam in remaining minutes

# Nordpool spot prices
@unpack(jfo, p, SpotPrice7D1S) # Expected spot price for one week, p[t]
p = [p[t] for t in SpotPrice7D1S]
T = length(p) # Number of hours

# Set up model
m = Model(solver=solver) # model with specified solver
@variables m begin
    Q[i=1:N,j=1:2,t=1:T], (lowerbound=0, upperbound=Qmax[i,j]) # Discharge (total min set in constraints)
    S[i=1:N,t=1:T], (lowerbound=Smin[i], upperbound=Smax[i]) # Spillage
    M[i=1:N,t=1:T], (lowerbound=0, upperbound=Mmax[i]) # Reservoir level
    P[t=1:T] # Total power generation
    SflowT[i=1:N,t=1:T] # Spill reaching station i at time t
    QflowT[i=1:N,t=1:T] # Flow reaching station i at time t
    Dp[i=1:N,t=1:T], (lowerbound=0) # Penalty on positive flow derivative
    Dm[i=1:N,t=1:T], (lowerbound=0) # Penalty on negative flow derivative
    Qtot[i=1:N,t=1:T] # Total discharge in station
end

# Objective function: maximize total profit minus penalty for changes
@objective(m, Max, sum(p[t]*P[t] for t=1:T) - sum(rho[i]*(Dp[i,t]+Dm[i,t]) for i=1:N, t=1:T))

# Constraints (constraint name, equation)
@constraints m begin
    Pwr[t=1:T], P[t] == sum(mu[i,j]*Q[i,j,t] for i=1:N, j=1:2) # Power generation
    EndRes[i=1:N],  M[i,T] == Mend[i] # End reservoir level
    HydBal[i=1:N,t=1:T], M[i,t] == (t==1 ? M0[i] :  M[i,t-1]) + V[i] - # Hydrobalance
        Qtot[i,t] - S[i,t] + sum(Aq[i,ii]*(QflowT[ii,t]+SflowT[ii,t]) for ii=1:N) +
        sum((t <= fqH[ii] ? Qavg[ii]*Aq[i,ii]  : 0) for ii=1:N) + # Ersätt med värde beräknat från V?
        sum((t == fqH[ii] + 1 ? Qavg[ii]*Aq[i,ii]*(60-fqM[ii])/60 : 0) for ii=1:N)
    QflowTime[i=1:N,t=1:T], QflowT[i,t] == fqM[i]/60 * (t-fqH[i]-1>0 ? Qtot[i,t-fqH[i]-1] : 0) +
        (60-fqM[i])/60 * (t-fqH[i]>0 ? Qtot[i,t-fqH[i]] : 0) # Total flow with delay
    SflowTime[i=1:N,t=1:T], SflowT[i,t] == fsM[i]/60 * (t-fsH[i]-1>0 ? S[i,t-fsH[i]-1] : 0) +
        (60-fsM[i])/60 * (t-fsH[i]>0 ? S[i,t-fsH[i]] : 0) # Total spill with delay
    Qlow[i=1:N,t=1:T], Qtot[i,t] >= Qmin[i] # Lower bound on total plant discharge
    Qprim[i=1:N,t=1:T], Qtot[i,t] - (t>1 ? Qtot[i,t-1] : 0) == Dp[i,t] - Dm[i,t] # Derivative of discharge
    Qsum[i=1:N,t=1:T], Qtot[i,t] == sum(Q[i,:,t]) # Sum for export
end

solution = solve(m)

# Get values from Jump variables
for s in ["M","S","Q","Qtot","P","SflowT","QflowT","Dp"]
    s = Symbol(s)
    @eval($s = getvalue($s))
end
revenue = getobjectivevalue(m)
