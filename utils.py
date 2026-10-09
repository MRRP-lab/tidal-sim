import numpy as np
import yaml
import pygame

EPSILON = 0.00001
DEBUG = False

### GEOMETRY

# returns the new heading for an agent that has hit a wall
# assumes bot r has moved through edge segment to the wrong side
# takes previous position (assumes to be outside obstacle) as input
# mirrors heading across normal
def bounce(edge, prev_c, new_c):
    x1, y1 = edge[0]
    x2, y2 = edge[1]

    invec = new_c - prev_c

    normal = np.array([y1-y2, x2-x1]) # pointing out
    nhat = normal / np.linalg.norm(normal)

    # https://math.stackexchange.com/questions/13261/how-to-get-a-reflection-vector
    r = invec - 2*np.dot(invec, nhat)*nhat

    heading = np.arctan2(r[1], r[0])

    return heading

# returns +1 if v2 is pointing to the left of an agent looking along v1
# return -1 otherwise
# assumes v1 and v2 are vectors centered on the origin
def vector_to_left(heading, vec):
    x, y = np.cos(heading), np.sin(heading)
    return np.sign(x*vec[1] - y*vec[0])

# same as vector_to_left but returns indices from list of points
def vector_to_left_inds(heading, pts):
    signs = vector_to_left(heading, pts)
    rind = np.where(signs <=0)
    lind = np.where(signs > 0)
    return rind, lind

# calc whether points are left or right of a given heading centered at the origin
def pts_left_right(heading, pts):
    n = pts.shape[0]
    perp = heading - (np.pi/2) # 90 degrees clockwise
    unit_perp = np.array([np.cos(perp), np.sin(perp)])
    dot_perp = np.dot(np.full((n,2),unit_perp), pts.T)
    diag_perp = np.diagonal(dot_perp)
    sign_perp = np.sign(diag_perp) # 1 means the light is to the right of the robot, -1 to the left, 0 directly ahead
    rind = np.where(sign_perp>=0)[0]
    lind = np.where(sign_perp<0)[0]

    return rind, lind # indices of points to right and left in input array pts

# cross product
def Cross2d(p,q):
        return p[0]*q[1] - p[1]*q[0]

def ShootRay(state, v1, v2):
    '''
    # find line intersection parameter of edge (v1,v2)
    # state :: (x,y,theta) initial point and angle of ray
    # (x,y,theta) -> Point -> Point -> Maybe (Double, Point)
    # theta is defined with 0 along the y axis
    # https://stackoverflow.com/questions/14307158/how-do-you-check-for-intersection-between-a-line-segment-and-a-line-ray-emanatin/32146853
    # https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect/565282#565282
    '''
    pt = np.array([state[0], state[1]])
    theta = state[2]

    # points on ray are (x1,y1) + t*r
    r = (np.cos(theta), np.sin(theta))
    # points on segment are (x2,y2) + u*s
    s = v2-v1
    rXs = Cross2d(r,s)

    # if ray and target edge are parallel, will get divide by zero
    if abs(rXs) < EPSILON:
        if DEBUG:
            print('divide by zero in ray shoot')
            print('shot from ',state,'to',v1,v2)
        raise ValueError
    else:
        u = Cross2d(v1-pt, r)/rXs
        t = Cross2d(v1-pt, s)/rXs
        pint = np.array([pt[0] + np.cos(theta)*t, pt[1] + np.sin(theta)*t])
        return t, u, pint, v1, v2 # return edge end points for ease of identifying edges crossed

# any theta will work unless parallel to an edge
def IsInPolyNoHoles(p, vs, theta = 0.):
    ''' test if point p is in poly using crossing number.
    Note: this does not work with holes
    '''
    intersects = 0
    state=(p[0],p[1],theta)
    psize = len(vs)
    int_data = []
    for j in range(psize):
        v1, v2 = np.array(vs[j]), np.array(vs[(j+1) % psize])
        try:
            t, u, pt, v1, v2 = ShootRay(state, v1, v2)
            if t>0 and (0 < u) and (u < 1):
                intersects += 1
                int_data.append([pt,v1,v2])
        except: # ray parallel to edge
            pass
    return (not (intersects%2 == 0)), int_data # return edges that intersect

### FILE HANDLING
#
# TODO maybe separate environments and robots completely for easier batch processing

def load_config(filename):
    try:
        with open(filename) as file:
            param_list = yaml.load(file,Loader=yaml.FullLoader)

        # unpack yaml (sections in config are just for organization); numbers
        # become floats, anything else (lists, null, true/false) is kept as-is
        params = {k: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
                  for section in param_list
                  for k, v in param_list[section].items()}

        # Data sanitization as needed
        for key in ["sim_time", "screen_size", "grid_num", "FPS", "seed"]:
            params[key] = int(params[key])

        return params
    except Exception as e:
        print("Error loading file: " + str(filename))
        print(e)
        raise Exception("Error loading file: " + str(filename))

# load environment
# currently only loads a list of polygonal obstacles
def load_env(filename):
    params = {}
    try:
        with open(filename) as file:
            all_params = yaml.load(file,Loader=yaml.FullLoader)
            obstacles = all_params["obstacles"]
        return obstacles
    except Exception as e:
        print("Error loading file: " + str(filename))
        print(e)
        raise Exception("Error loading file: " + str(filename))

### PYGAME

# function to update the fps on each iteration
def update_fps(clock, font):
    fps = str(int(clock.get_fps()))
    fps_text = font.render(fps, 1, pygame.Color("coral"))
    return fps_text
