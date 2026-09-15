function y=tmats_remedy_invalid_state(u)
% Same numerical/surge criteria used in the report, for early rejection only.
y=double(any(~isfinite(u)) || any(abs(u(1:3))>1e-9) || u(4)<=0 || u(5)>=200);
end
