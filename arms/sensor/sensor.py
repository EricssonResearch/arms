
import arms.sensor.tcp as tcp
import sys
import arms.utils.log as log
from arms.config import config as c
import numpy as np

"""
A simple implementation with an initialization that can take a different ip adress
if necessary.
The connect method connects and the disconnect method disconnects
the read method saves all the sensor values to the sensor.values attribute.
To access the values you type sensor.values.Fx or .Ty etc.
"""

class ValueStruct:
    def __init__(self):
        self.Fx = 0
        self.Fy = 0
        self.Fz = 0
        self.Tx = 0
        self.Ty = 0
        self.Tz = 0
    def __str__(self):
        return "Fx:" +str(self.Fx) +"\n" + "Fy:" +str(self.Fy) +"\n" + "Fz:" +str(self.Fz) +"\n"+\
               "Tx:" +str(self.Tx) +"\n" + "Tx:" +str(self.Ty) +"\n" + "Tx:" +str(self.Tz) +"\n"
    def __repr__(self):
        return self.__str__()
    
class Sensor:
    def __init__(self):
        sensor_config = c.var.data["sensor_config"]
        self.angle = sensor_config["angle"]
        self.zeroValues = ValueStruct()
        self.zeroValuesMain = ValueStruct()
        self.values = None
        self.ip = sensor_config["ip"]
        self.createRotationMatrix()
        #self.zero(True)
        self.switchZ = sensor_config["switchZ"]
        
    def createRotationMatrix(self, delta_angle = 0.0):
        self.angle += delta_angle
        theta = np.radians(self.angle)
        c, s = np.cos(theta), np.sin(theta)
        self.R = np.array(((c,-s), (s, c)))
        
    def connect(self):    
        tcp.sensorConnect(self.ip)
        log.sensor.info("Sensor connected at address:" + self.ip)
        
    def disconnect(self):
        tcp.sensorDisconnect()
        log.sensor.info("Sensor disconnected from address:" + self.ip)

    def read(self, main = False):
        self.values = tcp.sensorRead()
        if main:
            self.values.Fx -= self.zeroValuesMain.Fx
            self.values.Fy -= self.zeroValuesMain.Fy
            self.values.Fz -= self.zeroValuesMain.Fz
            self.values.Tx -= self.zeroValuesMain.Tx
            self.values.Ty -= self.zeroValuesMain.Ty
            self.values.Tz -= self.zeroValuesMain.Tz
        else:
            self.values.Fx -= self.zeroValues.Fx
            self.values.Fy -= self.zeroValues.Fy
            self.values.Fz -= self.zeroValues.Fz
            self.values.Tx -= self.zeroValues.Tx
            self.values.Ty -= self.zeroValues.Ty
            self.values.Tz -= self.zeroValues.Tz
        self.values.Fx, self.values.Fy = self.transform(self.values.Fx, self.values.Fy)
        self.values.Tx, self.values.Ty = self.transform(self.values.Tx, self.values.Ty)

        if switchZ:
            self.values.Fz *= -1
            self.values.Tz *= -1
        log.sensor.debug("Sensor values:")
        log.sensor.debug("Fx: " + str(self.values.Fx) + "N")
        log.sensor.debug("Fy: " + str(self.values.Fy) + "N")
        log.sensor.debug("Fz: " + str(self.values.Fz) + "N")
        log.sensor.debug("Tx: " + str(self.values.Tx) + "Nm")
        log.sensor.debug("Ty: " + str(self.values.Ty) + "Nm")
        log.sensor.debug("Tz: " + str(self.values.Tz) + "Nm")
       
    
    def zero(self, main = False):
        self.read()
        if main:
            self.zeroValuesMain.Fx = self.values.Fx
            self.zeroValuesMain.Fy = self.values.Fy
            self.zeroValuesMain.Fz = self.values.Fz
            self.zeroValuesMain.Tx = self.values.Tx
            self.zeroValuesMain.Ty = self.values.Ty
            self.zeroValuesMain.Tz = self.values.Tz
        else:
            self.zeroValues.Fx = self.values.Fx
            self.zeroValues.Fy = self.values.Fy
            self.zeroValues.Fz = self.values.Fz
            self.zeroValues.Tx = self.values.Tx
            self.zeroValues.Ty = self.values.Ty
            self.zeroValues.Tz = self.values.Tz

    def transform(self, x, y):
        X = np.array(([x],[y]))
        X = np.multiply(self.R, X)
        return X[0],X[1]
        

def main():
    #sys.path("/home")
    #sys.argv = ['build_ext', '--inplace']
    #exec('setup.py')
    tcp.sensorConnect("192.168.1.1")
    #for i in range(10):
    while True:
        try:
            r = tcp.sensorRead()
            print(r.Fx)
            print(r.Fy)
            print(r.Fz)
            print(r.Tx)
            print(r.Ty)
            print(r.Tz)
            time.sleep(0.5)
        except KeyboardInterrupt:
            break
        
        finally:
            tcp.sensorDisconnect()

if __name__ == "__main__":
    main()
