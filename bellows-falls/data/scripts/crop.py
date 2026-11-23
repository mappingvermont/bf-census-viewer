import sys
from PIL import Image
p,out,x0,y0,x1,y1,W = sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7]),int(sys.argv[7])
im=Image.open(p); w,h=im.size
c=im.crop((int(x0*w),int(y0*h),int(x1*w),int(y1*h)))
c=c.resize((W,int(W*c.size[1]/c.size[0])))
c.save(out,quality=85)
