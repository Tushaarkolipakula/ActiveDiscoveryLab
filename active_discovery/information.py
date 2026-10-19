"""Local Gaussian parameter-information design, not exact nonlinear EIG."""
import numpy as np
from .environment import trajectory_sensitivities


def gaussian_information(covariance, sensitivity, noise_std):
    """0.5 log det(I + L' J' J L / sigma²), with C = L L'.

    Exact for a linear observation model with Gaussian parameter uncertainty
    and independent Gaussian noise. Here both the linearization and C are
    local approximations. Singular covariance (absent terms) is supported.
    """
    c=np.asarray(covariance,dtype=float)
    j=np.asarray(sensitivity,dtype=float)
    if noise_std<=0 or c.ndim!=2 or c.shape[0]!=c.shape[1] or j.ndim!=2 or j.shape[1]!=len(c):
        raise ValueError('Invalid information-design dimensions or noise.')
    if not np.isfinite(c).all() or not np.isfinite(j).all():
        raise ValueError('Nonfinite information-design input.')
    if not np.allclose(c,c.T,atol=1e-10): raise ValueError('Covariance must be symmetric.')
    values,vectors=np.linalg.eigh((c+c.T)/2)
    if values.min() < -1e-10*max(1.,abs(values).max()): raise ValueError('Covariance must be positive semidefinite.')
    root=vectors*np.sqrt(np.maximum(values,0))[None,:]
    projected=j@root/noise_std
    sign,logdet=np.linalg.slogdet(np.eye(len(c))+projected.T@projected)
    if sign<=0: raise ValueError('Information matrix is not positive definite.')
    return max(0.,float(logdet)/2)


def information_components(fits,experiment,protocol):
    total=0.
    for fit in fits:
        if fit.weight==0: continue
        if fit.covariance is None: raise ValueError('Information design requires fitted covariance.')
        sensitivity=(fit.sensitivities(experiment,protocol.times) if hasattr(fit,'sensitivities')
                     else trajectory_sensitivities(fit.coefficients,experiment,protocol.times)[1])
        total+=fit.weight*gaussian_information(fit.covariance,sensitivity,protocol.noise_std)
    return {'structural':0.,'parameter':float(total),'total':float(total),
            'units':'nats (local Gaussian approximation)',
            'objective':'weighted conditional parameter information; excludes information about model identity'}
