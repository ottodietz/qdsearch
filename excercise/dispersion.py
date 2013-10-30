import math

def calculate_dispersion(wavelength,grooves):
        m=1 #grating order
        x=8.548 #spectro value: half angle
        f=486 # focal length
        phi=math.degrees(math.asin((m*wavelength*grooves/(2*10**6*math.cos(math.radians(x))))))
        dispersion=math.cos(math.radians(x+phi))*10**6/(grooves*f*m)
        return dispersion

def wvl(centerwvl,grooves):
        wavelength=[]
        pixel=1024
        for i in range(pixel+1):
            wavelength.append(i)
        width=26*10**-3
        wavelength[pixel/2]=centerwvl
        for i in range(pixel/2):
            wavelength[pixel/2-i-1]=wavelength[pixel/2-i]-width*calculate_dispersion(wavelength[pixel/2-i],grooves)
            wavelength[pixel/2+i+1]=wavelength[pixel/2+i]+width*calculate_dispersion(wavelength[pixel/2+i],grooves)
        return wavelength

wvl1 = wvl(900,600)
print "Bei 900nm/600er Grating sieht man von", min(wvl1)," bis ",max(wvl1)

wvl2 = wvl(895,1200)
print "Bei 895nm/1200er Grating sieht man von", min(wvl2)," bis ",max(wvl2)

