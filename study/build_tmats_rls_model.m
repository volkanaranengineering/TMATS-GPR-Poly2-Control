function build_tmats_rls_model(replaceExisting)
% Create the requested copy and add a passive online estimator subsystem.
root=fileparts(mfilename('fullpath'));
if nargin<1, replaceExisting=false; end
[MWS,RLS]=tmats_rls_setup(); %#ok<ASGLU>
src='GasTurbine_Dyn_Template_GPT'; mdl=[src '_RLS'];
target=fullfile(root,[mdl '.mdl']);
assert(~exist(target,'file') || replaceExisting,'RLS model already exists; refusing to overwrite it.');
if exist(target,'file'), copyfile(target,[target '.bak']); end
if bdIsLoaded(mdl), close_system(mdl,0); end
load_system(fullfile(root,[src '.mdl']));
set_param(src,'CloseFcn','');
save_system(src,target);
if bdIsLoaded(src), close_system(src,0); end
load_system(target);
set_param(mdl,'CloseFcn','','PreLoadFcn','tmats_rls_setup;', ...
    'Description','T-MATS reference with passive ARX(5,5,1) RLS acceleration observer. Run tmats_rls_setup first.');
add_block('simulink/Signal Routing/Bus Selector',[mdl '/RLS Reference signals'], ...
    'OutputSignals','PlantBus.Ndot,PlantErrors,PlantBus.Iter,PlantBus.C_Data.SMavail', ...
    'Position',[1310 650 1320 810]);
add_line(mdl,'IterativeSolver and InnerLoopPlant/1','RLS Reference signals/1','autorouting','on');
sub=[mdl '/RLS Acceleration Observer'];
add_block('built-in/Subsystem',sub,'Position',[1470 605 1760 845], ...
    'BackgroundColor','green');
inputNames={'Fuel_lbm_s','Ndot_rpm_s','FlowErrors','SolverIterations','StabilityMargin'};
for k=1:5
    add_block('simulink/Ports & Subsystems/In1',[sub '/' inputNames{k}], ...
        'Port',num2str(k),'Position',[35 35+60*k 65 55+60*k]);
end
add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[sub '/RLS ARX 5 5 1'], ...
    'FunctionName','tmats_rls_arx_sfun','Parameters','RLS','Position',[200 80 380 480]);
for k=1:5
    if k==4
        add_block('simulink/Signal Attributes/Data Type Conversion',[sub '/Iteration count to double'], ...
            'OutDataTypeStr','double','Position',[105 315 160 345]);
        add_line(sub,[inputNames{k} '/1'],'Iteration count to double/1');
        add_line(sub,'Iteration count to double/1',['RLS ARX 5 5 1/' num2str(k)]);
    else
        add_line(sub,[inputNames{k} '/1'],['RLS ARX 5 5 1/' num2str(k)]);
    end
end
outputNames={'Ndot_prediction','Innovation','Theta','CovarianceDiagonal','UpdateStatus','Regressor','FuelOffset'};
for k=1:7
    add_block('simulink/Ports & Subsystems/Out1',[sub '/' outputNames{k}], ...
        'Port',num2str(k),'Position',[480 45+60*k 510 65+60*k]);
    add_line(sub,['RLS ARX 5 5 1/' num2str(k)],[outputNames{k} '/1']);
end
add_line(mdl,'Simple PI controller/1','RLS Acceleration Observer/1','autorouting','on');
for k=1:4
    add_line(mdl,['RLS Reference signals/' num2str(k)],['RLS Acceleration Observer/' num2str(k+1)],'autorouting','on');
end
vars={'RLS_yhat','RLS_error','RLS_theta','RLS_Pdiag','RLS_status','RLS_phi','RLS_u0'};
for k=1:7
    sink(mdl,vars{k},['RLS Acceleration Observer/' num2str(k)],[1850 560+50*k 1950 585+50*k]);
end
sink(mdl,'RLS_reference','RLS Reference signals/1',[1370 890 1470 915]);
sink(mdl,'RLS_flowErrors','RLS Reference signals/2',[1370 940 1470 965]);
add_block('simulink/Signal Routing/Mux',[mdl '/Reference and Estimate'],'Inputs','2', ...
    'Position',[1775 975 1780 1025]);
add_line(mdl,'RLS Reference signals/1','Reference and Estimate/1','autorouting','on');
add_line(mdl,'RLS Acceleration Observer/1','Reference and Estimate/2','autorouting','on');
add_block('simulink/Sinks/Scope',[mdl '/Acceleration Reference vs RLS'],'Position',[1850 975 1930 1025]);
add_line(mdl,'Reference and Estimate/1','Acceleration Reference vs RLS/1');
set_param(mdl,'SimulationCommand','update');
save_system(mdl,target);
close_system(mdl,0);
fprintf('CREATED_RLS_MODEL: %s\n',target);
end

function sink(mdl,name,source,pos)
add_block('simulink/Sinks/To Workspace',[mdl '/' name],'VariableName',name, ...
    'SaveFormat','Timeseries','MaxDataPoints','inf','SampleTime','-1','Position',pos);
add_line(mdl,source,[name '/1'],'autorouting','on');
end
