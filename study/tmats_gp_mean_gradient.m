function [mu,gradient]=tmats_gp_mean_gradient(f,X)
% Exact posterior mean and input derivatives. f holds a compact model and scaledTraining.
m=f.model;z=bsxfun(@rdivide,bsxfun(@minus,X,m.inputMean),m.inputScale);
z=bsxfun(@rdivide,z,m.lengthScale');mu=zeros(size(X,1),1);gradient=zeros(size(X));
for k=1:size(X,1)
 delta=bsxfun(@minus,f.scaledTraining,z(k,:));w=m.outputScale*m.signalSD^2*exp(-.5*sum(delta.^2,2)).*m.alpha;
 mu(k)=m.outputMean+sum(w);
 if nargout>1,gradient(k,:)=sum(bsxfun(@times,delta,w),1)./(m.inputScale.*m.lengthScale');end
end
end
