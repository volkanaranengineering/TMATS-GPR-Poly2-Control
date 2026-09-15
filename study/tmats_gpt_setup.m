function MWS = tmats_gpt_setup()
% Initialize the GPT copy using the adjacent standard example's parameters.
root = fileparts(mfilename('fullpath'));
trunk = fileparts(root);
setupDir = fullfile(trunk,'TMATS_Examples','Example_GasTurbine_Dyn','SimSetup');
assert(exist(setupDir,'dir') == 7,'Missing standard example SimSetup: %s',setupDir);
addpath(genpath(fullfile(trunk,'TMATS_Library')));
% Isolate generic setup_* function names from other examples on the path.
oldDir = pwd;
restoreDir = onCleanup(@() cd(oldDir));
cd(setupDir);
MWS.engName = 'engine1';
MWS.top_level = root;
names = {'Solve_temp','Inputs','HPC','Shaft','Noz','HPT','Burner','Duct','Inlet'};
for k = 1:numel(names)
    MWS = feval(['setup_' names{k}], MWS);
end
end
