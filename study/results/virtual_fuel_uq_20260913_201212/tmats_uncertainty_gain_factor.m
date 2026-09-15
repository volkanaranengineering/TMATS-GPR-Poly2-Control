function factor=tmats_uncertainty_gain_factor(sigmaSetpoint,sigmaFeedback,sigmaReference)
% Relative predictive SD: factor=0.1 at max(SD)=3*sigmaReference.
validateattributes(sigmaReference,{'numeric'},{'scalar','real','finite','positive'});
ratio=max(sigmaSetpoint,sigmaFeedback)/sigmaReference;
factor=exp(-log(10)*(ratio/3).^2);
factor(~isfinite(ratio)|~isfinite(sigmaSetpoint)|~isfinite(sigmaFeedback)|sigmaSetpoint<0|sigmaFeedback<0)=0;
end
