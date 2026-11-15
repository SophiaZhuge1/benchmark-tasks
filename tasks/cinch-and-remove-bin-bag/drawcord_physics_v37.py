"""Force-based sliding drawcord and passive cord-lock approximation.

This is a lumped, uncalibrated model, not explicit rope/hem contact. Forces
follow the gradient of routed cord length and are applied to dynamic rigid
hem markers and cord ends. No poses or simulation success flags are changed.
"""
import numpy as np

def routed_length_gradient(points):
    delta=np.diff(points,axis=0);length=np.linalg.norm(delta,axis=1)
    direction=delta/np.maximum(length[:,None],1e-9)
    gradient=np.zeros_like(points);gradient[:-1]-=direction;gradient[1:]+=direction
    return float(length.sum()),gradient

class SlidingDrawcord:
    def __init__(self,positions,stiffness=40.,damping=.03,lock_friction=.15,exit_index=None,handle_count=1):
        self.handle_count=handle_count
        self.n=len(positions)-handle_count;self.k=stiffness;self.d=damping;self.lock_friction=lock_friction
        self.routes=[]
        start=self.n//4 if exit_index is None else int(exit_index)
        if handle_count==2:
            # One continuous loop, with a pull-out bight at each opposite slit.
            # Both hands load the entire sewn hem through cord tension.
            opposite=(start+self.n//2)%self.n
            half0=[(start+i)%self.n for i in range(self.n//2+1)]
            half1=[(opposite+i)%self.n for i in range(self.n//2+1)]
            self.routes.append(np.array([self.n,*half0,self.n+1,*half1,self.n]))
        elif handle_count==1:
            handle=self.n
            hem=[(start+i)%self.n for i in range(self.n+1)]
            self.routes.append(np.array([handle,*hem,handle]))
        else:raise ValueError('Only one or two drawstring bights are supported')
        self.rest=[routed_length_gradient(positions[r])[0]+.002 for r in self.routes]
        self.lock_perimeter=float('inf');self.max_extension=0.;self.last={}
    def forces(self,positions,velocities,dt=1/240):
        gradients=[];extensions=[];rates=[];lengths=[]
        for route,rest in zip(self.routes,self.rest):
            length,g=routed_length_gradient(positions[route]);G=np.zeros_like(positions);np.add.at(G,route,g)
            gradients.append(G);extensions.append(length-rest);rates.append(float((G*velocities).sum()));lengths.append(length)
            self.max_extension=max(self.max_extension,max(0.,length-rest))
        route=np.r_[np.arange(self.n),0];perimeter,g=routed_length_gradient(positions[route]);G=np.zeros_like(positions);np.add.at(G,route,g)
        if max(self.last.get('tensions',[0.]))>self.lock_friction:self.lock_perimeter=min(self.lock_perimeter,perimeter+.002)
        if np.isfinite(self.lock_perimeter):
            gradients.append(G);extensions.append(perimeter-self.lock_perimeter);rates.append(float((G*velocities).sum()))
        # Implicit Euler solve for coupled unilateral routed-length springs.
        # Predicted elongation x + dt*v contributes k*dt*v to the RHS;
        # omitting that term removes the backward-Euler velocity response.
        # This avoids explicit stiff-spring instability without clipping forces.
        gradients=np.array(gradients);extensions=np.array(extensions);rates=np.array(rates)
        mass=np.r_[np.full(self.n,.001),np.full(self.handle_count,.006)]
        if self.handle_count==1:mass[3*self.n//4]=.006
        W=np.einsum('aij,bij,i->ab',gradients,gradients,1/mass)
        A=np.eye(len(extensions))+(dt*self.d+dt*dt*self.k)*W
        rhs=self.k*extensions+(dt*self.k+self.d)*rates
        active=np.where((extensions+dt*rates>0)&(rhs>0))[0];T=np.zeros(len(extensions))
        while len(active):
            candidate=np.linalg.solve(A[np.ix_(active,active)],rhs[active])
            if np.all(candidate>=0):T[active]=candidate;break
            active=active[candidate>=0]
        out=-np.einsum('a,aij->ij',T,gradients)
        self.last={'lengths':lengths,'tensions':T[:1].tolist(),'perimeter':perimeter,'lock_perimeter':self.lock_perimeter if np.isfinite(self.lock_perimeter) else None,'lock_tension':float(T[1]) if len(T)>1 else 0.,'max_extension':self.max_extension,'net_force':out.sum(0).tolist()}
        return out
