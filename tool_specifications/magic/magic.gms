$Title   M A G I C   Power Scheduling Problem   (MAGIC,SEQ=12)

$Ontext

A number of power stations are committed to meet demand for a particular
day. three types of generators having different operating characteristics
are available.  Generating units can be shut down or operate between
minimum and maximum output levels.  Units can be started up or closed down
in every demand block.


Garver, L L, Power Scheduling by Integer Programming,
Tariff-Rates-Power-Generation-Problem, IEEE Trans. Power Apparatus
and Systems, 81, 730-735, 1963

Day, R E, and Williams, H P, MAGIC: The design and use of an interactive
modeling language for mathematical programming. Tech. rep., Department
Business Studies, University of Edinburgh, 1982.

Williams, H P, Model Building in Mathematical Programming. John Wiley
and Sons, 1978.

$Offtext

$iftheni %system.filesys% == UNIX $set SLASH /
$else $set SLASH \
$endif


 Sets  t  demand blocks / 12pm-6am, 6am-9am, 9am-3pm, 3pm-6pm, 6pm-12pm /
       g  generators    / type-1, type-2, type-3 /

Alias(g, g_);

 Parameters dem(t)  demand (1000MW)   / 12pm-6am  15, 6am-9am   30, 9am-3pm   25, 3pm-6pm  40, 6pm-12pm   27 /
            dur(t)  duration (hours)  / 12pm-6am   6, 6am-9am    3, 9am-3pm    6, 3pm-6pm    3, 6pm-12pm   6 /

 Set param / min-pow  '(1000MW)'
             max-pow  '(1000MW)'
             cost-min '(¤/h)'
             cost-inc '(¤/h/MW)'
             start    '(¤)'
             number   '(units)'
             inv-cost '¤/kW'
          /

 Parameter data(g, param)  generation data ;
 Parameter number(g) number of generators built;

*******************************************************************************
$ontext
 Table data(g,param)  generation data

         min-pow  max-pow  cost-min  cost-inc  start    number  inv-cost

 type-1    .85      2.0      1000       2.0     2000      12    1000
 type-2   1.25      1.75     2600       1.3     1000      10    1200
 type-3   1.5       4.0      3000       3.0      500       5    2000
;

$gdxout 'input/data.gdx'
$unload data
$gdxout
$exit
$offtext
*******************************************************************************

$gdxin 'input/data.gdx'
$loaddc data
$iftheni not %INVEST% == 'yes'
    $$gdxin 'input/investments.gdx'
    $$loaddc number
$endif
$gdxin

 Parameters peak     peak power (1000MW)
            ener(t)  energy demand in load block (1000MWh)
            tener    total energy demanded (1000MWh)
            lf       load factor ;



  peak = smax(t, dem(t));  ener(t) = dur(t)*dem(t);  tener = sum(t, ener(t));  lf = tener/(peak*24);
  display peak, tener, lf, ener;

$eject
 Variables  x(g,t)  generator output (1000MW)
            n(g,t)  number of generators in use
            s(g,t)  number of generators started up
            k(g)    number of generators built
            cost    total operating cost (¤)

$iftheni %USE_MIP% == 'yes'
 Integer Variables k;
$ifi not %INVEST% == 'yes'
 Integer Variables n;
$endif
 Positive Variable s;

 Equations pow(t)    demand for power (1000MW)
           res(t)    spinning reserve requirements (1000MW)
           st(g,t)   start-up definition
           minu(g,t) minimum generation level (1000MW)
           maxu(g,t) maximum generation level (1000MW)
           totcap(g,t) total generation capacity
           totcap2(g) distribute investments
           cdef      cost definition (¤);

 pow(t)..  sum(g, x(g,t)) =g= dem(t);

 res(t)..  sum(g, data(g,"max-pow")*n(g,t)) =g= 1.15*dem(t);

 st(g,t).. s(g,t) =g= n(g,t) - n(g,t--1);

 minu(g,t)..  x(g,t) =g= data(g,"min-pow")*n(g,t);

 maxu(g,t)..  x(g,t) =l= data(g,"max-pow")*n(g,t);

 totcap(g,t) .. n(g,t) =l= k(g);
 totcap2(g) ..  k(g) =l= 0.5 * sum(g_, k(g_));

 cdef.. cost =e= sum((g,t),
                    dur(t)*data(g,"cost-min")*n(g,t)
                    + data(g,"start")*s(g,t)
                    + 1000*dur(t)*data(g,"cost-inc")*(x(g,t)
                    - data(g,"min-pow")*n(g,t))
                 )
$iftheni %INVEST% == 'yes'
                 + sum(g, k(g) * 1000 * data(g, 'inv-cost'))
$endif
;

$ifi not %INVEST% == 'yes'
    k.fx(g) = data(g, 'number');


 Model william /
    pow
    res
    st
    minu
    maxu
$iftheni %INVEST% == 'yes'
    totcap
    totcap2
$endif
    cdef
/;

william.optcr = 0;

$iftheni %USE_MIP% == 'yes'
 Solve william minimizing cost using mip;
$else
 Solve william minimizing cost using lp;
$endif

 Parameter rep  summary report;

    rep(t,"demand")    =  dem(t);
    rep(t,"spinning")  =  sum(g, data(g,"max-pow")*n.l(g,t));
    rep(t,"start-ups") =  sum(g, s.l(g,t));
    rep(t,"m-cost")    = -pow.m(t)/dur(t)/1000;

 Display rep;

 execute_unload 'output/report.gdx', rep;

$iftheni %INVEST% == 'yes'
    number(g) = k.l(g);
    execute_unload 'output/investments.gdx', number;
$endif

*execute_unload 'output/dump.gdx';

