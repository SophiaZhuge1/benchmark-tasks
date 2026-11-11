"""Check nominal demo waypoint chains against the actual YAM URDF (no physics).

This is a geometric IK check, not a grasp, load, collision or success certificate.
"""
import json
import numpy as np
from yam_arena import ik, station
from yam_arena.constants import FINGER_OPEN
from yam_arena.demo import ArmPlan, Waypoint
import task as t


def paths():
    top=t.TOP
    left=[(.18,.185,top+.136),(.18,.185,top+.066),(.18,.185,top+.111)]
    left += [(x,.185,top+.111) for x in (.21,.23,.25,.27,.29,.31)]
    recovery=left+[(.18,.185,top+.126),(.18,.185,top+.166),(.22,-.055,top+.166)]
    recovery += [(.22,-.055,top+.066+h) for h in (.06,.03,.01,.002)]
    recovery += [(.22,-.055,top+.118),(.18,.28,top+.16)]
    delivery=left+[(.425,.185,top+.111)]
    delivery += [(.425,.185,top+.066+h) for h in (.06,.03,.01,.002)]
    delivery += [(.425,.185,top+.118),(.20,.28,top+.16)]
    right=[(.18,-.28,top+.16),(.22,-.055,top+.189),(.22,-.055,top+.129),
           (.22,-.055,top+.189),(.18,-.28,top+.17)]
    right += [(.22,-.055,top+.128+h) for h in (.06,.03,.01,.002)]
    right += [(.22,-.055,top+.18),(.18,-.28,top+.16)]
    return [('left_recovery','left',recovery),('left_delivery','left',delivery),('right_lid','right',right)]


def main():
    result={}
    for name,side,points in paths():
        plan=ArmPlan([Waypoint(1.,p,FINGER_OPEN,f'{name}_{i}',0.) for i,p in enumerate(points)],station.BASES[side])
        legal=True
        for k in range(round(plan.duration*20)+1):
            q=np.asarray(plan.action7(k/20)[0])[:6]
            legal &= bool(np.all(q>=ik.LOWER-1e-9) and np.all(q<=ik.UPPER+1e-9))
        result[name]={'nominal_waypoints':len(points),'worst_ik_mm':round(plan.worst_ik_mm,4),
                      'worst_ik_deg':round(plan.worst_ik_deg,4),'joint_limits_ok':legal}
    result['physics_tested']=False
    print(json.dumps(result,indent=2))
    for name,values in result.items():
        if isinstance(values,dict):
            assert values['joint_limits_ok'] and values['worst_ik_mm']<.5 and values['worst_ik_deg']<.1, name
    return result


if __name__=='__main__': main()
