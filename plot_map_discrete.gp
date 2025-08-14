#!/usr/bin/gnuplot --persist

set terminal pngcairo size 800,600 enhanced font 'Verdana,10'
set datafile separator ","

# Parâmetros
index = sprintf("{/Symbol f}_{%s}", ARGV[3])
input_file = ARGV[1]
output_file = ARGV[2]

set title index font ',18'
set output output_file

# Remove a escala contínua
unset colorbox

# Legenda fora, com mais espaço
set key outside right top spacing 1.5

# Paleta original
set palette defined ( \
    0 '#440154', 1 '#482878', 2 '#3e4a89', 3 '#31688e', \
    4 '#26828e', 5 '#1f9e89', 6 '#35b779', 7 '#6ece58', \
    8 '#b5de2b', 9 '#fee825' )

# Plotando cada cluster mantendo o índice de cor original
plot \
    input_file every ::1 using 1:($4==0?$2:1/0):4 with points pt 5 ps .75 lc palette title "Cluster 1", \
    ''          every ::1 using 1:($4==1?$2:1/0):4 with points pt 5 ps .75 lc palette title "Cluster 2", \
    ''          every ::1 using 1:($4==2?$2:1/0):4 with points pt 5 ps .75 lc palette title "Cluster 3", \
    ''          every ::1 using 1:($4==3?$2:1/0):4 with points pt 5 ps .75 lc palette title "Cluster 4"
