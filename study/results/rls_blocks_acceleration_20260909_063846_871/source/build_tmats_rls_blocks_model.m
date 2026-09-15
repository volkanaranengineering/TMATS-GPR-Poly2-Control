function build_tmats_rls_blocks_model()
% Build an ARX(5,5,1) RLS observer using ordinary Simulink blocks only.
root=fileparts(mfilename('fullpath')); tmats_rls_setup;
src='GasTurbine_Dyn_Template_GPT_RLS'; mdl=[src '_Blocks'];
target=fullfile(root,[mdl '.mdl']);
if bdIsLoaded(mdl), close_system(mdl,0); end
if exist(target,'file'), copyfile(target,[target '.bak']); end
load_system(fullfile(root,[src '.mdl'])); save_system(src,target);
if bdIsLoaded(src), close_system(src,0); end
load_system(target);
set_param(mdl,'Description','Basic-block RLS ARX(5,5,1) fuel-to-acceleration observer. No estimator S-function or MATLAB Function.');
s=[mdl '/RLS Acceleration Observer'];
% Recreating subsystem ports removes their external connections. Record the
% complete top-level netlist before changing ports, then restore it below.
connections={};
topBlocks=find_system(mdl,'SearchDepth',1,'Type','Block');
for i=1:numel(topBlocks)
    if strcmp(topBlocks{i},mdl), continue; end
    ports=get_param(topBlocks{i},'PortHandles');
    for j=1:numel(ports.Inport)
        line=get_param(ports.Inport(j),'Line');
        if line<0, continue; end
        source=get_param(line,'SrcPortHandle');
        if source<0, continue; end
        sourceBlock=get_param(source,'Parent');
        connections(end+1,:)={sourceBlock(numel(mdl)+2:end),get_param(source,'PortNumber'), ...
            topBlocks{i}(numel(mdl)+2:end),j}; %#ok<AGROW>
    end
end
Simulink.SubSystem.deleteContents(s);
ins={'Fuel_lbm_s','Ndot_rpm_s','FlowErrors','SolverIterations','StabilityMargin'};
for k=1:5
    b(s,'Ports & Subsystems/In1',ins{k},[20 30+70*k 50 50+70*k],'Port',num2str(k));
    b(s,'Discrete/Zero-Order Hold',['Sample ' ins{k}],[90 30+70*k 155 50+70*k],'SampleTime','RLS.Ts');
    w(s,[ins{k} '/1'],['Sample ' ins{k} '/1']);
end
b(s,'Signal Attributes/Data Type Conversion','Iterations double',[180 305 235 335],'OutDataTypeStr','double');
w(s,'Sample SolverIterations/1','Iterations double/1');
% Validity logic is encapsulated for readability.
g=[s '/Validity and update gate']; b(s,'Ports & Subsystems/Subsystem','Validity and update gate',[285 90 485 340]);
Simulink.SubSystem.deleteContents(g); buildGate(g);
sources={'Sample Fuel_lbm_s/1','Sample Ndot_rpm_s/1','Sample FlowErrors/1','Iterations double/1','Sample StabilityMargin/1','Phi column/1'};
for k=1:5, w(s,sources{k},['Validity and update gate/' num2str(k)]); end
% Equilibrium fuel offset tracks preparation, then remains frozen.
b(s,'Discrete/Unit Delay','Fuel offset state',[600 385 680 425],'SampleTime','RLS.Ts','InitialCondition','3');
sw(s,'Track preparation offset',[520 390 565 440],'Sample Fuel_lbm_s/1','Validity and update gate/3','Fuel offset state/1');
w(s,'Track preparation offset/1','Fuel offset state/1');
sumblock(s,'Fuel deviation','+-',[725 390 765 430],'Sample Fuel_lbm_s/1','Track preparation offset/1');
b(s,'Math Operations/Gain','Normalize fuel',[795 390 865 430],'Gain','1/RLS.uScale'); w(s,'Fuel deviation/1','Normalize fuel/1');
b(s,'Math Operations/Gain','Normalize acceleration',[520 480 620 520],'Gain','1/RLS.yScale'); w(s,'Sample Ndot_rpm_s/1','Normalize acceleration/1');
% Five explicit delays for each measured history; a fault freezes each delay.
for j=1:2
    if j==1, prefix='Y'; first='Normalize acceleration/1'; else, prefix='U'; first='Normalize fuel/1'; end
    for k=1:5
        name=sprintf('%s delay %d',prefix,k); gate=sprintf('%s history switch %d',prefix,k);
        xx=520+(k-1)*170; yy=580+(j-1)*150;
        b(s,'Discrete/Unit Delay',name,[xx+75 yy xx+135 yy+35],'SampleTime','RLS.Ts','InitialCondition','0');
        if k==1, source=first; else, source=sprintf('%s delay %d/1',prefix,k-1); end
        sw(s,gate,[xx yy xx+45 yy+45],[name '/1'],'Validity and update gate/2',source);
        w(s,[gate '/1'],[name '/1']);
    end
end
b(s,'Signal Routing/Mux','History vector',[1540 580 1545 870],'Inputs','10');
for k=1:5
    b(s,'Math Operations/Gain',sprintf('Negative Y %d',k),[1420 560+k*40 1480 585+k*40],'Gain','-1');
    w(s,sprintf('Y delay %d/1',k),sprintf('Negative Y %d/1',k));
    w(s,sprintf('Negative Y %d/1',k),sprintf('History vector/%d',k));
    w(s,sprintf('U delay %d/1',k),sprintf('History vector/%d',k+5));
end
b(s,'Math Operations/Reshape','Phi column',[1590 680 1670 720],'OutputDimensionality','Customize','OutputDimensions','[10 1]');
w(s,'History vector/1','Phi column/1');
w(s,'Phi column/1','Validity and update gate/6');
b(s,'Discrete/Unit Delay','Theta state',[650 55 745 100],'SampleTime','RLS.Ts','InitialCondition','zeros(10,1)');
b(s,'Discrete/Unit Delay','P state',[650 160 745 205],'SampleTime','RLS.Ts','InitialCondition','RLS.P0*eye(10)');
r=[s '/RLS matrix arithmetic']; b(s,'Ports & Subsystems/Subsystem','RLS matrix arithmetic',[850 50 1070 280]);
Simulink.SubSystem.deleteContents(r); buildRecursion(r);
ss={'Theta state/1','P state/1','Phi column/1','Normalize acceleration/1'};
for k=1:4, w(s,ss{k},['RLS matrix arithmetic/' num2str(k)]); end
sw(s,'Accept theta update',[520 35 570 85],'RLS matrix arithmetic/1','Validity and update gate/1','Theta state/1');
sw(s,'Accept P update',[520 150 570 200],'RLS matrix arithmetic/2','Validity and update gate/1','P state/1');
w(s,'Accept theta update/1','Theta state/1'); w(s,'Accept P update/1','P state/1');
b(s,'Sources/Constant','Invalid prediction',[1120 320 1180 350],'Value','NaN');
sw(s,'Mask invalid prediction',[1230 280 1280 330],'Invalid prediction/1','Validity and update gate/2','RLS matrix arithmetic/3');
b(s,'Math Operations/Gain','Physical prediction',[1330 280 1430 320],'Gain','RLS.yScale'); w(s,'Mask invalid prediction/1','Physical prediction/1');
sumblock(s,'Physical innovation','+-',[1480 280 1520 320],'Sample Ndot_rpm_s/1','Physical prediction/1');
b(s,'Math Operations/Reshape','P vector',[1120 80 1190 120],'OutputDimensionality','1-D array'); w(s,'P state/1','P vector/1');
b(s,'Signal Routing/Selector','P diagonal',[1250 70 1340 125],'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'},'Indices','1:11:100','InputPortWidth','100'); w(s,'P vector/1','P diagonal/1');
b(s,'Discrete/Unit Delay','Update count',[660 270 740 305],'SampleTime','RLS.Ts','InitialCondition','0');
b(s,'Signal Attributes/Data Type Conversion','Enable double',[520 265 590 300],'OutDataTypeStr','double'); w(s,'Validity and update gate/1','Enable double/1');
sumblock(s,'Count increment','++',[610 315 650 350],'Update count/1','Enable double/1'); w(s,'Count increment/1','Update count/1');
b(s,'Signal Attributes/Data Type Conversion','Fault double',[1120 390 1190 425],'OutDataTypeStr','double'); w(s,'Validity and update gate/2','Fault double/1');
b(s,'Signal Routing/Mux','Status vector',[1250 380 1255 475],'Inputs','3');
w(s,'Enable double/1','Status vector/1'); w(s,'Fault double/1','Status vector/2'); w(s,'Update count/1','Status vector/3');
outs={'Ndot_prediction','Innovation','Theta','CovarianceDiagonal','UpdateStatus','Regressor','FuelOffset'};
ss={'Physical prediction/1','Physical innovation/1','Theta state/1','P diagonal/1','Status vector/1','Phi column/1','Fuel offset state/1'};
for k=1:7
    b(s,'Ports & Subsystems/Out1',outs{k},[1850 30+100*k 1880 50+100*k],'Port',num2str(k)); w(s,ss{k},[outs{k} '/1']);
end
bad=find_system(s,'LookUnderMasks','all','FollowLinks','on','BlockType','S-Function'); assert(isempty(bad));
bad=find_system(s,'LookUnderMasks','all','FollowLinks','on','BlockType','MATLABSystem'); assert(isempty(bad));
topLines=find_system(mdl,'FindAll','on','SearchDepth',1,'Type','line');
for i=1:numel(topLines)
    if ishandle(topLines(i)), delete_line(topLines(i)); end
end
for i=1:size(connections,1)
    add_line(mdl,sprintf('%s/%d',connections{i,1},connections{i,2}), ...
        sprintf('%s/%d',connections{i,3},connections{i,4}),'autorouting','on');
end
observerPorts=get_param(s,'PortHandles');
assert(all(cell2mat(get_param(observerPorts.Inport,'Line'))>0));
assert(all(cell2mat(get_param(observerPorts.Outport,'Line'))>0));
set_param(mdl,'SimulationCommand','update'); save_system(mdl,target); close_system(mdl,0);
fprintf('BASIC_BLOCKS_MODEL_CREATED: %s\n',target);
end

function buildRecursion(s)
names={'Theta','P','Phi','Y'};
for k=1:4, b(s,'Ports & Subsystems/In1',names{k},[20 40+90*k 50 60+90*k],'Port',num2str(k)); end
b(s,'Math Operations/Gain','P prior',[110 195 185 235],'Gain','1/RLS.lambda'); w(s,'P/1','P prior/1');
trans(s,'Phi transpose',[115 300 185 340],'Phi/1');
matrixProduct(s,'P phi',[245 190 300 235],'P prior/1','Phi/1');
matrixProduct(s,'Phi P phi',[350 190 410 235],'Phi transpose/1','P phi/1');
b(s,'Sources/Constant','One',[350 100 395 130],'Value','1');
sumblock(s,'Denominator','++',[460 180 505 230],'One/1','Phi P phi/1');
b(s,'Math Operations/Product','Gain vector',[560 180 630 230],'Inputs','*/','Multiplication','Element-wise(.*)');
w(s,'P phi/1','Gain vector/1'); w(s,'Denominator/1','Gain vector/2');
matrixProduct(s,'Prior prediction',[250 365 325 415],'Phi transpose/1','Theta/1');
sumblock(s,'Innovation','+-',[395 365 445 415],'Y/1','Prior prediction/1');
matrixProduct(s,'Theta correction',[685 350 750 400],'Gain vector/1','Innovation/1');
sumblock(s,'Next theta','++',[810 350 860 400],'Theta/1','Theta correction/1');
matrixProduct(s,'K phi transpose',[685 175 760 225],'Gain vector/1','Phi transpose/1');
b(s,'Sources/Constant','Identity',[685 70 755 105],'Value','eye(10)');
sumblock(s,'Joseph J','+-',[810 165 865 215],'Identity/1','K phi transpose/1');
matrixProduct(s,'J P',[920 160 975 205],'Joseph J/1','P prior/1');
trans(s,'J transpose',[915 70 980 105],'Joseph J/1');
matrixProduct(s,'J P J transpose',[1030 160 1110 205],'J P/1','J transpose/1');
trans(s,'K transpose',[810 265 880 305],'Gain vector/1');
matrixProduct(s,'K K transpose',[1030 265 1110 310],'Gain vector/1','K transpose/1');
sumblock(s,'Joseph covariance','++',[1160 185 1220 235],'J P J transpose/1','K K transpose/1');
trans(s,'Covariance transpose',[1245 285 1320 325],'Joseph covariance/1');
sumblock(s,'Symmetric sum','++',[1360 190 1420 240],'Joseph covariance/1','Covariance transpose/1');
b(s,'Math Operations/Gain','Next P',[1465 190 1530 240],'Gain','0.5'); w(s,'Symmetric sum/1','Next P/1');
outs={'Updated theta','Updated P','Prior estimate'}; ss={'Next theta/1','Next P/1','Prior prediction/1'};
for k=1:3, b(s,'Ports & Subsystems/Out1',outs{k},[1600 100+130*k 1630 120+130*k],'Port',num2str(k)); w(s,ss{k},[outs{k} '/1']); end
end

function buildGate(s)
names={'Fuel','Acceleration','Errors','Iterations','Margin','Phi'};
for k=1:6, b(s,'Ports & Subsystems/In1',names{k},[15 20+70*k 45 40+70*k],'Port',num2str(k)); end
b(s,'Signal Routing/Mux','Reference vector',[90 80 95 360],'Inputs','5');
for k=1:5, w(s,[names{k} '/1'],['Reference vector/' num2str(k)]); end
b(s,'Math Operations/Abs','Absolute reference',[125 100 185 140]); w(s,'Reference vector/1','Absolute reference/1');
compare(s,'Finite entries','<','Inf',[225 90 315 135],'Absolute reference/1');
b(s,'Logic and Bit Operations/Logical Operator','All finite',[355 90 425 135],'Operator','AND','Inputs','1'); w(s,'Finite entries/1','All finite/1');
b(s,'Math Operations/Abs','Absolute flow error',[130 200 200 235]); w(s,'Errors/1','Absolute flow error/1');
b(s,'Math Operations/MinMax','Maximum flow error',[235 195 310 235],'Function','max','Inputs','1'); w(s,'Absolute flow error/1','Maximum flow error/1');
compare(s,'Flow converged','<=','RLS.flowTolerance',[350 190 445 235],'Maximum flow error/1');
compare(s,'Iterations valid','<','RLS.iterationLimit',[130 285 230 325],'Iterations/1');
compare(s,'Fuel valid','>=','0',[280 280 360 320],'Fuel/1');
compare(s,'Margin valid','>','0',[400 280 485 320],'Margin/1');
b(s,'Logic and Bit Operations/Logical Operator','Good reference',[535 90 605 275],'Operator','AND','Inputs','5');
ss={'All finite/1','Flow converged/1','Iterations valid/1','Fuel valid/1','Margin valid/1'};
for k=1:5, w(s,ss{k},['Good reference/' num2str(k)]); end
b(s,'Logic and Bit Operations/Logical Operator','Bad reference',[645 90 700 130],'Operator','NOT'); w(s,'Good reference/1','Bad reference/1');
b(s,'Discrete/Unit Delay','Fault memory',[650 200 720 240],'SampleTime','RLS.Ts','InitialCondition','false');
b(s,'Logic and Bit Operations/Logical Operator','Fault latched',[770 110 840 175],'Operator','OR','Inputs','2');
w(s,'Bad reference/1','Fault latched/1'); w(s,'Fault memory/1','Fault latched/2'); w(s,'Fault latched/1','Fault memory/1');
b(s,'Logic and Bit Operations/Logical Operator','Healthy',[880 100 940 140],'Operator','NOT'); w(s,'Fault latched/1','Healthy/1');
b(s,'Sources/Digital Clock','Sample clock',[535 350 605 390],'SampleTime','RLS.Ts');
compare(s,'Preparation','<','RLS.startTime-1e-9',[650 340 755 385],'Sample clock/1');
b(s,'Logic and Bit Operations/Logical Operator','Started',[800 345 860 380],'Operator','NOT'); w(s,'Preparation/1','Started/1');
trans(s,'Phi transpose',[130 440 210 480],'Phi/1');
matrixProduct(s,'Phi energy',[255 440 330 480],'Phi transpose/1','Phi/1');
compare(s,'Excited','>','RLS.minPhiNorm^2',[380 435 490 480],'Phi energy/1');
b(s,'Logic and Bit Operations/Logical Operator','Enable update',[980 290 1060 405],'Operator','AND','Inputs','3');
w(s,'Healthy/1','Enable update/1'); w(s,'Started/1','Enable update/2'); w(s,'Excited/1','Enable update/3');
b(s,'Logic and Bit Operations/Logical Operator','Track offset',[980 460 1060 515],'Operator','AND','Inputs','2');
w(s,'Healthy/1','Track offset/1'); w(s,'Preparation/1','Track offset/2');
ss={'Enable update/1','Fault latched/1','Track offset/1'}; outs={'Enable','Fault','Preparing'};
for k=1:3, b(s,'Ports & Subsystems/Out1',outs{k},[1130 100+140*k 1160 120+140*k],'Port',num2str(k)); w(s,ss{k},[outs{k} '/1']); end
end

function b(s,lib,n,pos,varargin)
add_block(['simulink/' lib],[s '/' n],'Position',pos,varargin{:});
end
function w(s,a,z), add_line(s,a,z,'autorouting','on'); end
function sw(s,n,pos,a,control,z)
b(s,'Signal Routing/Switch',n,pos,'Criteria','u2 ~= 0'); w(s,a,[n '/1']); w(s,control,[n '/2']); w(s,z,[n '/3']);
end
function sumblock(s,n,signs,pos,a,z)
b(s,'Math Operations/Sum',n,pos,'Inputs',signs); w(s,a,[n '/1']); w(s,z,[n '/2']);
end
function matrixProduct(s,n,pos,a,z)
b(s,'Math Operations/Product',n,pos,'Inputs','**','Multiplication','Matrix(*)'); w(s,a,[n '/1']); w(s,z,[n '/2']);
end
function trans(s,n,pos,a)
b(s,'Math Operations/Math Function',n,pos,'Operator','transpose'); w(s,a,[n '/1']);
end
function compare(s,n,op,value,pos,a)
b(s,'Logic and Bit Operations/Compare To Constant',n,pos,'relop',op,'const',value); w(s,a,[n '/1']);
end


