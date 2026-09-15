function [acceleration,uncertainty,interval95,latentSD] = predict_tmats_exact_gpr(model,speed,fuel)
% Inputs: matching vectors of rpm and lbm/s. Outputs: rpm/s.
% uncertainty is predictive response SD; latentSD excludes fitted noise.
% model is the exported struct in exact_gpr_model.mat (no toolbox needed).
assert(isnumeric(speed)&&isnumeric(fuel)&&numel(speed)==numel(fuel),'Inputs must be matching numeric vectors.');
X=[speed(:) fuel(:)]; assert(all(isfinite(X(:))),'Inputs must be finite.');
Z=bsxfun(@rdivide,bsxfun(@minus,X,model.inputMean),model.inputScale);
A=bsxfun(@rdivide,model.Z,model.lengthScale');
B=bsxfun(@rdivide,Z,model.lengthScale');
D=max(0,bsxfun(@plus,sum(A.^2,2),sum(B.^2,2)')-2*A*B');
K=model.signalSD^2*exp(-D/2);
acceleration=model.outputMean+model.outputScale*(K'*model.alpha);
V=model.L\K;
latentVar=max(0,model.signalSD^2-sum(V.^2,1)');
latentSD=model.outputScale*sqrt(latentVar);
uncertainty=model.outputScale*sqrt(latentVar+model.noiseSD^2);
interval95=[acceleration-1.95996398454005*uncertainty acceleration+1.95996398454005*uncertainty];
end
