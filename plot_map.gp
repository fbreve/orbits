!#/usr/bin/gnuplot --persist

# print "input: ", ARGV[1]
# print "output: ", ARGV[2]

set terminal pngcairo size 800,600 enhanced font 'Verdana,10'
set datafile separator ","
set key autotitle columnhead

# The third argument passed in the command line
index = sprintf("{/Symbol f}_{%s}", ARGV[3])

# Now use 'index' in the title instead of the now commented form
set title index font ',18'
# set title '{/Symbol f}_{1}' font ',18'

# Retrieve the input and output filenames directly from command-line arguments
input_file = ARGV[1]
output_file = ARGV[2]

# Set the output file
set output output_file

# Define Viridis color palette
set palette defined ( 0 '#440154', 1 '#482878', 2 '#3e4a89', 3 '#31688e', \
                      4 '#26828e', 5 '#1f9e89', 6 '#35b779', 7 '#6ece58', \
                      8 '#b5de2b', 9 '#fee825' )

# Plot the data from input_file using the specified columns
plot input_file every ::1 using 1:2:4 with points pt 5 ps .75 palette notitle
