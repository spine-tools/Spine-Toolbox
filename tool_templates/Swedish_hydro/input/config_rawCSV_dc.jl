using JSON

dc = Dict("name" => "Swedish_hydro", "path" => pwd())

open("rawCSV.json", "w+") do f
        write(f, JSON.json(dc))
     end
