orbit_series = zeros(22288,400);
for i=1:22288
    filename = "series\" + (i-1) + ".csv";
    serie = load(filename);
    orbit_series(i,:) = serie(1,2:end)';
end
save orbit_series orbit_series