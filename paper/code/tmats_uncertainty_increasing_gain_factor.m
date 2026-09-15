function factor=tmats_uncertainty_increasing_gain_factor(sigmaSetpoint,sigmaFeedback,sigmaReference)
% Unit gain through one reference SD; smooth increase to two at three SDs.
validateattributes(sigmaReference,{'numeric'},{'scalar','real','finite','positive'});
ratio=max(sigmaSetpoint,sigmaFeedback)/sigmaReference;
x=max(0,min(1,(ratio-1)/2));
factor=1+x.^2.*(3-2*x);
% Infinite uncertainty saturates at two; invalid numerical SD is not a query.
factor(isnan(sigmaSetpoint)|isnan(sigmaFeedback)|sigmaSetpoint<0|sigmaFeedback<0)=0;
end
