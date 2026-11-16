"""Symmetric sliding sleeve approximation for an ordinary factory tape.

Each hem seam marker follows the locally adjacent portion of a freely moving
closed tape. Normal spring forces keep the tape inside the seam; a symmetric
viscous/Coulomb tangential force approximates hem friction. There is no ratchet,
minimum remembered perimeter, knot switch, fixed bight, or scripted object pose.
Rigid tape links and their joints/contact handle tape tension and self-contact.
This is a development approximation, not a calibrated sewing/material model.
"""
import numpy as np

class SlidingHem:
    def __init__(self,hem,tape,hem_mass,tape_mass,stiffness=15.,damping=.006,friction=.2):
        self.n=len(hem);self.m=len(tape);self.hm=hem_mass;self.tm=tape_mass
        self.k=stiffness;self.d=damping;self.mu=friction
        self.segment=np.argmin(np.linalg.norm(hem[:,None]-tape[None,:],axis=2),axis=1)
        self.last={}

    def forces(self,hem,tape,hem_velocity,tape_velocity,dt):
        hf=np.zeros_like(hem);tf=np.zeros_like(tape);max_gap=0.
        for i in range(self.n):
            # Local tracking avoids jumping to a different strand at crossings.
            ids=(self.segment[i]+np.arange(-2,3))%self.m
            ends=(ids+1)%self.m
            segments=tape[ends]-tape[ids]
            lengths=np.linalg.norm(segments,axis=1)
            if np.any(lengths<1e-7):raise ValueError('Collapsed tape segment')
            u=np.clip(np.einsum('ij,ij->i',hem[i]-tape[ids],segments)/(lengths**2),0.,1.)
            closest=tape[ids]+u[:,None]*segments
            j=int(np.argmin(np.linalg.norm(hem[i]-closest,axis=1)))
            a,b=ids[j],ends[j];t=float(u[j]);self.segment[i]=a
            tangent=segments[j]/lengths[j]
            error=hem[i]-closest[j];max_gap=max(max_gap,float(np.linalg.norm(error)))
            relative=hem_velocity[i]-(1-t)*tape_velocity[a]-t*tape_velocity[b]
            normal=relative-tangent*np.dot(relative,tangent)
            inverse_mass=1/self.hm+((1-t)**2+t*t)/self.tm
            force=-(self.k*error+(self.d+dt*self.k)*normal)/(1+(dt*self.d+dt*dt*self.k)*inverse_mass)
            # Friction always opposes sliding, in either direction. At rest it
            # adds no invented locking spring; closure must survive on physics.
            speed=float(np.dot(relative,tangent))
            magnitude=min(abs(speed)/(dt*inverse_mass),self.mu*float(np.linalg.norm(force)))
            force-=tangent*np.sign(speed)*magnitude
            hf[i]+=force;tf[a]-=(1-t)*force;tf[b]-=t*force
        self.last={'max_sleeve_gap_m':max_gap,'net_force':(hf.sum(0)+tf.sum(0)).tolist(),'one_way_lock':False}
        return hf,tf
