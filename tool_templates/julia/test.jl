tic()
using DataFrames
using CSV

df = CSV.read("input/branch.csv")

println(df)
println("elapsed time = ", toq(), " seconds")
