function [mu,gradient]=tmats_poly2_mean_gradient(f,X)
% Full quadratic in standardized N, acceleration, inlet T and inlet P.
m=f.poly;mean=m.inputMean(:)';scale=m.inputScale(:)';c=m.coefficients(:);
z=bsxfun(@rdivide,bsxfun(@minus,X,mean),scale);Phi=[ones(size(X,1),1) z z.^2];
for k=1:6,Phi(:,9+k)=z(:,m.pairs(k,1)).*z(:,m.pairs(k,2));end
mu=Phi*c;gradient=zeros(size(X));
if nargout>1
 gradient=bsxfun(@plus,c(2:5)',bsxfun(@times,2*z,c(6:9)'));
 for k=1:6,i=m.pairs(k,1);j=m.pairs(k,2);gradient(:,i)=gradient(:,i)+c(9+k)*z(:,j);gradient(:,j)=gradient(:,j)+c(9+k)*z(:,i);end
 gradient=bsxfun(@rdivide,gradient,scale);
end
end
