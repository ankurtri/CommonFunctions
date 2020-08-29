import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os


DISTANCE= 1
TOLERANCE = 1e-1

for POW in [i/10.0 for i in range(2,100)]:

    OUTPUT = [];
    
    CANVASrANGE = [i/200.0 for i in range(0,400)]
    CANVAS_LENGTH = 100
    
    mid_x = 0.5*(max(CANVASrANGE) + min(CANVASrANGE))
    mid_y = 0.5*(max(CANVASrANGE) + min(CANVASrANGE))
             
    for i in CANVASrANGE:
        for j in CANVASrANGE:
            if np.abs(np.power(np.abs(i-mid_x),POW)+np.power(np.abs(j-mid_y),POW)-1)<=TOLERANCE:
                OUTPUT.append((POW,i,j))
    
    OUTPUT = pd.DataFrame(OUTPUT,columns=['POW','x','y'])
    OUTPUT['x'] = (OUTPUT['x']*CANVAS_LENGTH).map(lambda x: int(x))
    OUTPUT['y'] = (OUTPUT['y']*CANVAS_LENGTH).map(lambda x: int(x))
    
    Indices = np.array(OUTPUT[['x','y']])
    OutImage = np.zeros(shape=(max(OUTPUT['x']+1),max(OUTPUT['y']+1)))
    
    OutImage[Indices[:,0],Indices[:,1]] = 1
            
    plt.imsave("Pow_"+np.str(POW).zfill(4)+".jpg",OutImage)
