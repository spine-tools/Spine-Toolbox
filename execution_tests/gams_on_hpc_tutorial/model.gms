* Convert CSV to GDX (VERY SIMPLE, no headers)
$call csv2gdx input.csv id=data index=1 value=2 colCount=2 output=data.gdx

* Declare symbols
set i;
parameter data(*), value(i);

* Load data
$gdxin data.gdx
$load data i=Dim1
$gdxin

display i, data;

* Copy values
value(i) = data(i);

* Compute total
scalar total;
total = sum(i, value(i));

display total;

* Write output file
file fout /output.txt/;
put fout;

put "Results:" /;
loop(i,
    put i.tl, " ", value(i):8:2 /;
);

put "Total = ", total:8:2 /;

putclose fout;
