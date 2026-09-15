function [fuel,sd,latentSD]=predict_tmats_environment_gpr(model,X)
% X columns: speed rpm, acceleration rpm/s, inlet total temperature K, pressure kPa.
assert(size(X,2)==4 && all(isfinite(X(:))));
Z=bsxfun(@rdivide,bsxfun(@minus,X,model.inputMean),model.inputScale);
A=bsxfun(@rdivide,model.Z,model.lengthScale');B=bsxfun(@rdivide,Z,model.lengthScale');
D=max(0,bsxfun(@plus,sum(A.^2,2),sum(B.^2,2)')-2*A*B');
K=model.signalSD^2*exp(-.5*D);
fuel=model.outputMean+model.outputScale*(K'*model.alpha);
if nargout>1
 V=model.L\K;variance=max(0,model.signalSD^2-sum(V.^2,1)');
 latentSD=model.outputScale*sqrt(variance);sd=model.outputScale*sqrt(variance+model.noiseSD^2);
end
end
