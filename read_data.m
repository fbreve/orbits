function dynamicmap = read_data(filename, dataLines)
%IMPORTFILE Import data from a text file
%  DYNAMICMAP1 = IMPORTFILE(FILENAME) reads data from text file FILENAME
%  for the default selection.  Returns the data as a table.
%
%  DYNAMICMAP1 = IMPORTFILE(FILE, DATALINES) reads data for the
%  specified row interval(s) of text file FILENAME. Specify DATALINES as
%  a positive scalar integer or a N-by-2 array of positive scalar
%  integers for dis-contiguous row intervals.
%
%  Example:
%  dynamicmap1 = importfile("C:\Users\fbrev\Documents\Acadêmico\Simulações\Matlab\orbits\dynamic_map.csv", [2, Inf]);
%
%  See also READTABLE.
%
% Auto-generated by MATLAB on 24-Oct-2024 18:24:40

%% Input handling

% If dataLines is not specified, define defaults
if nargin < 2
    dataLines = [2, Inf];
end

%% Set up the Import Options and import the data
opts = delimitedTextImportOptions("NumVariables", 4);

% Specify range and delimiter
opts.DataLines = dataLines;
opts.Delimiter = ",";

% Specify column names and types
opts.VariableNames = ["semimajor_axis", "eccentricity", "file_name", "cluster_index"];
opts.VariableTypes = ["double", "double", "string", "double"];

% Specify file level properties
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% Specify variable properties
opts = setvaropts(opts, "file_name", "WhitespaceRule", "preserve");
opts = setvaropts(opts, "file_name", "EmptyFieldRule", "auto");

% Import the data
dynamicmap = readtable(filename, opts);

end