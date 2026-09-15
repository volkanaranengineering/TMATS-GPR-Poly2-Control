function [fuel,uncertainty,interval95,latentSD] = predict_tmats_inverse_gpr(model,speed,acceleration)
% Inverse GP: speed [rpm], acceleration [rpm/s] -> fuel flow [lbm/s].
% All outputs are lbm/s; uncertainty is response SD, latentSD excludes noise.
% Scalar or matching vector inputs; base MATLAB only, no clipping.
assert(isfield(model,'mapping') && strcmp(model.mapping,'speed_acceleration_to_fuel'), ...
    'Load the inverse model from inverse_gpr_model.mat.');
validateattributes(speed,{'numeric'},{'real','finite','vector','nonempty'});
validateattributes(acceleration,{'numeric'},{'real','finite','vector','nonempty'});
assert(numel(speed)==numel(acceleration),'Speed and acceleration must have matching lengths.');
X=[speed(:) acceleration(:)];
Z=bsxfun(@rdivide,bsxfun(@minus,X,model.inputMean),model.inputScale);
A=bsxfun(@rdivide,model.Z,model.lengthScale');
B=bsxfun(@rdivide,Z,model.lengthScale');
D=max(0,bsxfun(@plus,sum(A.^2,2),sum(B.^2,2)')-2*A*B');
K=model.signalSD^2*exp(-D/2);
fuel=model.outputMean+model.outputScale*(K'*model.alpha);
V=model.L\K;
latentVar=max(0,model.signalSD^2-sum(V.^2,1)');
latentSD=model.outputScale*sqrt(latentVar);
uncertainty=model.outputScale*sqrt(latentVar+model.noiseSD^2);
interval95=[fuel-1.95996398454005*uncertainty fuel+1.95996398454005*uncertainty];
end
