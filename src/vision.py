from PIL import Image, ImageChops, ImageOps
from math import sqrt, atan2
from io import BytesIO
from itertools import combinations

# CONSTANTS
imwidth = 640
imheight = 480
cropbox = (200,0,450,480) #find better values
cropwidth = 250
cropheight = 480
blob_size_min = 5
blob_size_max = 36
blob_size_ideal = 15
ideal_angle_1 = 0.33
ideal_angle_2 = -2.81
angle_allowed_1 = (0.0, 1.1)
angle_allowed_2 = (-3.14, -2.04)
size_weight = 1.0
angle_weight = 15.0
movement_threshold_left = 30 #find better value
movement_threshold_right = 25  # ^ same
separation_threshold = 20      # ^ same


# ***** UTITLITY CLASSES *****
class ConnectedComponent:
    def __init__(self):
        self.coords = set()
    def __repr__(self):
        return "<position "+str(self.avg_position())+", size "+str(self.size()+">")
    def addcoord(self, x, y):
        self.coords.add((x,y))
    def contains(self, x, y):
        return (x,y) in self.coords
    def size(self):
        return len(self.coords)
    def avg_position(self):
        avgx = float(sum([c[0] for c in self.coords])) / float(self.size())
        avgy = float(sum([c[1] for c in self.coords])) / float(self.size())
        return (avgx,avgy)
        
class Calibration:
    leftpos = (-1,-1)
    rightpos = (-1,-1)
    separation = -1
    def calibrate(camera):
        p1, p2 = capture_to_positions(camera)
        #left dot has higher y-value
        Calibration.leftpos = p1 if p1[1]>p2[1] else p2
        Calibration.rightpos = p1 if p2 is Calibration.leftpos else p2
        Calibration.separation = _dot_separation(p1,p2)


# ***** UTILITY FUNCTIONS *****
def _get_owning_component(blobs, x, y):
    for blob in blobs:
        if blob.contains(x,y): return blob
    return None

def _eligible_move(pxarr, x, y):
    return x>=0 and x<cropwidth and y>=0 and y<cropheight and pxarr[x,y]>1

def _blob_size_filter(blob):
    return blob_size_min <= blob.size() <= blob_size_max

def _get_angle(pos1, pos2):
    return atan2(pos2[1]-pos1[1], pos2[0]-pos1[0])

def _angle_filter(theta):
    #theta = _get_angle(pos1, pos2)
    #can be between 90 and 150 degrees, or its quadrant-4 counterpart
    return angle_allowed_1[0] < theta < angle_allowed_1[1] \
        or angle_allowed_2[0] < theta < angle_allowed_2[1]

def _dot_separation(pos1, pos2):
    return sqrt( (pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2 )


# ***** MAIN LOGIC *****
def differentiate_images(imon, imoff):
    imon = imon.crop(cropbox)
    imoff = imoff.crop(cropbox)
    imdiff = ImageChops.difference(imon,imoff).convert('L')
    imdiff = ImageOps.autocontrast(imdiff)
    return imdiff.point(lambda x: 0 if x<190 else 255)
    #return imdiff


def find_connected_components(img):
    pxarr = img.load()
    blobs = []
    search_dirs = ((1,0),(0,1),(-1,0),(0,-1))
    for x in xrange(cropwidth):
        for y in xrange(cropheight):
            if pxarr[x,y]<1 or _get_owning_component(blobs,x,y) != None:
                continue
            #bright and not classified; therefore classify that shiznit
            currentcomp = ConnectedComponent()
            currentcomp.addcoord(x,y)
            blobs.append(currentcomp)
            posstack = [(x,y)]
            while len(posstack) > 0:
                tmpx, tmpy = posstack.pop()
                for dx,dy in search_dirs:
                    newx, newy = tmpx+dx, tmpy+dy
                    if _eligible_move(pxarr,newx,newy) and not (newx,newy) in posstack \
                            and _get_owning_component(blobs,newx,newy) == None:
                        posstack.append((newx,newy))
                        currentcomp.addcoord(newx,newy)
    return blobs


def image_process(image1, image2, verbose_output=False):
    imdiff = differentiate_images(image1,image2)
    raw_blobs = find_connected_components(imdiff)
    blobs = filter(_blob_size_filter, raw_blobs)
    if verbose_output:
        print "Vision: "+str(len(raw_blobs))+" raw connected components"
        print "Vision: "+str(len(blobs))+" correctly sized blobs"
    if len(blobs) <= 2:
        good_positions = [b.avg_position() for b in blobs]
    else:
        combos = combinations(blobs, 2)
        pos_costs = []
        for b1,b2 in combos:
            pos1, pos2 = b1.avg_position(), b2.avg_position()
            theta = _get_angle(pos1, pos2)
            if not _angle_filter(theta):
                continue
            # size factor = worst-sized blob in the pairing
            # expected < 10
            size_factor = max(abs(b1.size()-blob_size_ideal), \
                              abs(b2.size()-blob_size_ideal))
            # angle factor = angular distance from desired
            # expected < 0.8
            angle_factor = min(abs(theta-ideal_angle_1), \
                               abs(theta-ideal_angle_2))
            cost = size_factor*size_weight + angle_factor*angle_weight
            pos_costs.append( ((pos1,pos2), cost) )
        if verbose_output:
            print "Vision: "+str(len(combos))+" pairs of blobs"
            print "Vision: "+str(len(pos_costs))+" at correct angles"
        good_positions = min(pos_costs, key=lambda pc: pc[1])
    if verbose_output:
        return (good_positions, image1, image2, imdiff, raw_blobs, blobs)
    else:
        return good_positions



def capture_to_positions(camera, f_laseron, f_laseroff, verbose=False):
    imfile1, imfile2 = BytesIO(), BytesIO()
    f_laseron()
    camera.capture(imfile1, format='jpeg', use_video_port=True)
    f_laseroff()
    camera.capture(imfile2, format='jpeg', use_video_port=True)
    imfile1.seek(0)
    imfile2.seek(0)
    im1 = Image.open(imfile1)
    im2 = Image.open(imfile2)
    return image_process(im1, im2, verbose_output=verbose)


   
def is_dropoff(pos1, pos2, verbose=False):
    bad_signs = 0
    left, right = (pos1, pos2) if pos1[1]>pos2[1] else (pos2, pos1)
    if _dot_separation(left, Calibration.leftpos) > movement_threshold_left:
        if verbose: print "Vision: left dot looks like a dropoff"
        bad_signs += 1
    if _dot_separation(right, Calibration.rightpos) > movement_threshold_right:
        if verbose: print "Vision: right dot looks like a dropoff"
        bad_signs += 1
    if _dot_separation(left,right)-Calibration.separation>separation_threshold:
        if verbose: print "Vision: separation distance looks like a dropoff"
        bad_signs += 1
    return bad_signs > 0
    