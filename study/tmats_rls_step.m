function [theta,P,gain,innovation] = tmats_rls_step(theta,P,phi,y,lambda)
% Exponentially weighted RLS, with Joseph-form covariance update.
% Prediction must be evaluated BEFORE calling this update.
prior=P/lambda;
gain=prior*phi/(1+phi'*prior*phi);
innovation=y-phi'*theta;
theta=theta+gain*innovation;
A=eye(numel(theta))-gain*phi';
P=A*prior*A'+gain*gain';
P=(P+P')/2;
end
