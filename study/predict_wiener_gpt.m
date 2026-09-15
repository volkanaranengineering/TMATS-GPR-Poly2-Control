function [speed_rpm,linear_state_output] = predict_wiener_gpt(fuel_lbm_s,modelFile)
% Simulate the saved Wiener model from its zero normalized initial state.
% fuel_lbm_s: uniformly sampled column vector at the saved sample interval.
% modelFile: full path to best_wiener_model.mat. No identification toolbox is
% required for this coefficient-based calculation (only load/filter/polyval).
% Start near the saved equilibrium; arbitrary initial states need initialization.
validateattributes(fuel_lbm_s,{'numeric'},{'vector','real','finite'});
saved=load(modelFile,'coefficients');
c=saved.coefficients;
u=(fuel_lbm_s(:)-c.scaling.input_offset)/c.scaling.input_scale;
linear_state_output=filter(c.B,c.F,u);
speed_rpm=c.scaling.output_offset+c.scaling.output_scale* ...
    polyval(c.quadratic_descending,linear_state_output);
end
