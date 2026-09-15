function run = run_tmats_gpt(scenario)
% Repeatable closed-loop scenarios for GasTurbine_Dyn_Template_GPT (R2018b).
% Fields: name, time_s, speed_rpm, altitude_ft, stop_s, sample_s,
% interpolation ('linear' or 'zoh'). Omitted fields use example defaults.
% Outputs: native MAT data, a flat CSV, metadata JSON and a quick-look PNG.
if nargin == 0, scenario = struct(); end
assert(isstruct(scenario) && isscalar(scenario),'Scenario must be a scalar struct.');
defaults = struct('name','baseline','time_s',[0 5 10 100], ...
    'speed_rpm',[10000 10000 9000 9000],'altitude_ft',[0 0 0 0], ...
    'stop_s',10.5,'sample_s',0.015,'interpolation','linear');
fields = fieldnames(scenario);
assert(all(ismember(fields,fieldnames(defaults))),'Unknown scenario field.');
fields = fieldnames(defaults);
for k=1:numel(fields)
    if ~isfield(scenario,fields{k}), scenario.(fields{k})=defaults.(fields{k}); end
end
assert(ischar(scenario.name) && ~isempty(regexp(scenario.name,'^[A-Za-z0-9_-]+$','once')), ...
    'Use only letters, digits, underscore and hyphen in the scenario name.');
validateattributes(scenario.time_s,{'numeric'},{'vector','real','finite','increasing','nonnegative'});
t=scenario.time_s(:);
assert(numel(t)>=2 && t(1)==0,'Time must start at zero and contain at least two points.');
validateattributes(scenario.speed_rpm,{'numeric'},{'vector','real','finite','positive','numel',numel(t)});
validateattributes(scenario.altitude_ft,{'numeric'},{'vector','real','finite'});
if isscalar(scenario.altitude_ft), scenario.altitude_ft=repmat(scenario.altitude_ft,size(t)); end
assert(numel(scenario.altitude_ft)==numel(t),'Altitude and time lengths must match.');
validateattributes(scenario.stop_s,{'numeric'},{'scalar','real','finite','positive'});
validateattributes(scenario.sample_s,{'numeric'},{'scalar','real','finite','positive'});
assert(t(end)>=scenario.stop_s,'Input profiles must cover the simulation duration.');
assert(abs(scenario.stop_s/scenario.sample_s-round(scenario.stop_s/scenario.sample_s))<1e-8, ...
    'Stop time must be an integer multiple of sample_s.');
assert(ismember(scenario.interpolation,{'linear','zoh'}),'Interpolation must be linear or zoh.');
if strcmp(scenario.interpolation,'zoh')
    assert(all(abs(t/scenario.sample_s-round(t/scenario.sample_s))<1e-8), ...
        'Zero-order-hold profile times must align with the sample interval.');
end
root=fileparts(mfilename('fullpath'));
mdl='GasTurbine_Dyn_Template_GPT';
assert(~bdIsLoaded(mdl),'Close the GPT model before using this isolated runner (save any edits first).');
oldPath=path;
restorePath=onCleanup(@() path(oldPath));
MWS=tmats_gpt_setup();
MWS.in.t_vec=t'; MWS.in.Ndmd=scenario.speed_rpm(:)';
MWS.in.Alt=scenario.altitude_ft(:)'; MWS.in.SimTime=scenario.stop_s;
MWS.Solve.T=scenario.sample_s;
% Retain the standard 10000 rpm initial state; demand is a command, not a trim.
load_system(fullfile(root,[mdl '.mdl']));
set_param(mdl,'CloseFcn','');
closeModel=onCleanup(@() close_system(mdl,0));
% Replace only the two input sources in memory to give explicit interpolation.
replaceSource(mdl,'Model Source',[t scenario.altitude_ft(:)],scenario.interpolation,scenario.sample_s);
replaceSource(mdl,'Model Source1',[t scenario.speed_rpm(:)],scenario.interpolation,scenario.sample_s);
addSink(mdl,'GPT_Nrequest','N_request','Model Source1/1');
addSink(mdl,'GPT_Nsensed','N_sensed','1st order  Sensor/1');
% Log the final flow residuals outside the iterative subsystem, once per time step.
add_block('simulink/Signal Routing/Bus Selector',[mdl '/GPT_ErrorSelector'], ...
    'OutputSignals','PlantErrors','Position',[1300 410 1305 450]);
add_line(mdl,'IterativeSolver and InnerLoopPlant/1','GPT_ErrorSelector/1','autorouting','on');
addSink(mdl,'GPT_Errors','FlowErrors','GPT_ErrorSelector/1');
input=Simulink.SimulationInput(mdl);
input=input.setVariable('MWS',MWS);
input=input.setModelParameter('ReturnWorkspaceOutputs','on','LimitDataPoints','off');
started=tic;
raw=sim(input);
elapsed=toc(started);
assert(isempty(raw.ErrorMessage),'Simulation failed: %s',raw.ErrorMessage);
time=raw.Nmech.Time(:);
data=table(time,'VariableNames',{'time_s'});
names=raw.who;
for k=1:numel(names)
    if ~ismember(names{k},{'tout','logsout','yout'})
        data=flatten(data,raw.get(names{k}),names{k},time);
    end
end
values=data{:,:};
assert(all(isfinite(values(:))),'Nonfinite output detected; do not use this run for identification.');
assert(numel(time)==round(scenario.stop_s/scenario.sample_s)+1 && ...
    abs(time(end)-scenario.stop_s)<1e-9,'Incomplete output time grid.');
errors=raw.FlowErrors.Data;
meta=struct('model',mdl,'model_file',get_param(mdl,'FileName'), ...
    'matlab',version,'scenario',scenario,'mode','closed_loop_speed_command', ...
    'solver',get_param(mdl,'Solver'),'initial_speed_rpm',MWS.Solve.N_IC, ...
    'samples',numel(time),'wall_seconds',elapsed, ...
    'max_abs_flow_error',max(abs(errors(:))), ...
    'flow_error_tolerance',MWS.Solve.C_Lim, ...
    'max_iterations',max(raw.Iterations.Data(:)), ...
    'iteration_limit',MWS.Solve.Max_Iter,'all_exported_values_finite',true);
meta.converged=meta.max_abs_flow_error<=MWS.Solve.C_Lim && meta.max_iterations<MWS.Solve.Max_Iter;
meta.units=struct('time','s','Nmech','rpm','N_request','rpm','N_sensed','rpm', ...
    'Alt','ft','Wf','lbm/s','Fnet','lbf','SFC','(lbm/hr)/lbf', ...
    'station_W','lbm/s','station_Tt','degR','station_Pt','psia', ...
    'station_ht','BTU/lbm','station_FAR','lbm_fuel/lbm_air','SMavail','percent');
meta.note='Synthetic closed-loop data; startup is not trimmed. Check convergence and discard startup as appropriate.';
outDir=fullfile(root,'results',[scenario.name '_' datestr(now,'yyyymmdd_HHMMSS_FFF')]);
assert(~exist(outDir,'dir'),'Output directory already exists.');
mkdir(outDir);
save(fullfile(outDir,'run.mat'),'raw','MWS','scenario','meta','data','-v7.3');
writetable(data,fullfile(outDir,'data.csv'));
fid=fopen(fullfile(outDir,'metadata.json'),'w');
assert(fid>=0,'Cannot write metadata.');
fwrite(fid,jsonencode(meta),'char'); fclose(fid);
f=figure('Visible','off','Color','w','Position',[50 50 1000 750]);
closeFigure=onCleanup(@() close(f));
subplot(3,1,1); plot(time,data.N_request,time,data.Nmech); grid on;
ylabel('Speed (rpm)'); legend('Demand','Shaft','Location','best'); title(scenario.name,'Interpreter','none');
subplot(3,1,2); plot(time,data.Wf); grid on; ylabel('Fuel (lbm/s)');
subplot(3,1,3); plot(time,data.Fnet); grid on; ylabel('Net thrust (lbf)'); xlabel('Time (s)');
print(f,fullfile(outDir,'overview.png'),'-dpng','-r130');
run=struct('directory',outDir,'data',data,'metadata',meta,'raw',raw);
fprintf('Saved %d samples to %s\n',numel(time),outDir);
fprintf('Max flow residual %.4g; max iterations %g; convergence pass: %d\n', ...
    meta.max_abs_flow_error,meta.max_iterations,meta.converged);
if ~meta.converged
    warning('TMATS:GPT:Convergence','Run saved for diagnosis; convergence checks failed.');
end
end

function replaceSource(mdl,name,profile,method,sourceStep)
block=[mdl '/' name];
pos=get_param(block,'Position');
ports=get_param(block,'PortHandles');
line=get_param(ports.Outport,'Line');
signalName=get_param(line,'Name');
dest=get_param(line,'DstPortHandle');
delete_line(line);
delete_block(block);
interp='on'; if strcmp(method,'zoh'), interp='off'; end
sampleTime='0';
if strcmp(method,'zoh')
    sampleTime='MWS.Solve.T';
    % Place discontinuities between sample hits to avoid floating-point equality
    % deciding which bit is applied. A discrete source only changes on sample hits.
    profile(2:end,1)=profile(2:end,1)-sourceStep/4;
end
add_block('simulink/Sources/From Workspace',block,'Position',pos, ...
    'VariableName',mat2str(profile,17),'Interpolate',interp,'SampleTime',sampleTime, ...
    'OutputAfterFinalValue','Holding final value');
ports=get_param(block,'PortHandles');
for k=1:numel(dest), add_line(mdl,ports.Outport,dest(k),'autorouting','on'); end
set_param(get_param(ports.Outport,'Line'),'Name',signalName);
end

function addSink(mdl,name,variable,source)
add_block('simulink/Sinks/To Workspace',[mdl '/' name], ...
    'VariableName',variable,'SaveFormat','Timeseries','MaxDataPoints','inf', ...
    'SampleTime','-1','Position',[1350 500 1420 530]);
add_line(mdl,source,[name '/1'],'autorouting','on');
end

function data=flatten(data,value,prefix,time)
if isa(value,'timeseries')
    assert(isequal(value.Time(:),time),'Time grid differs for %s.',prefix);
    x=value.Data;
    if ~value.IsTimeFirst, x=permute(x,[ndims(x) 1:ndims(x)-1]); end
    x=reshape(x,numel(time),[]);
    for j=1:size(x,2)
        name=prefix; if size(x,2)>1, name=sprintf('%s_%d',prefix,j); end
        data.(matlab.lang.makeValidName(name))=x(:,j);
    end
elseif isstruct(value)
    fields=fieldnames(value);
    for k=1:numel(fields), data=flatten(data,value.(fields{k}),[prefix '_' fields{k}],time); end
end
end
