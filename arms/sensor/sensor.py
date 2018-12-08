
import arms.sensor.tcp as tcp
import sys
import arms.utils.log as log
from arms.config import config as c
import numpy as np
from threading import Thread
from time import sleep

"""
A simple implementation with an initialization that can take a different ip adress
if necessary.
The connect method connects and the disconnect method disconnects
the read method saves all the sensor values to the sensor.values attribute.
To access the values you type sensor.values.Fx or .Ty etc.
"""
class PingThread(Thread):
    """ thread to repeatedly poll hardware
      sleeptime: time to sleep between pollfunc calls
      pollfunc: function to repeatedly call to poll hardware
    """
    def __init__(self,sleeptime,ping):
        super().__init__()
        self.sleeptime = sleeptime
        self.ping = ping
        self._running = True

    def run(self):
        while self._running:
            self.ping()
            sleep(self.sleeptime)

    def terminate(self):
        self._running = False
        


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
        self.pingThread = PingThread(0.9,self.ping)
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

    def start_ping(self):
        self.pingThread.start()

    def ping(self):
        tcp.ping()

    def stop_ping(self):
        self.pingThread.terminate()

    def adjust(self, stepSize):
        self.read()
        dx = dy = 0
        """Detects the torques and moves according to what's detected. TODO: determine threshold"""
        if self.values.Tx >= 1:
            dy = -stepSize
        elif self.values.Tx <= -1:
            dy = stepSize
                    
        if self.values.Ty >= 1:
            dx = -stepSize
        elif self.values.Ty <= -1:
            dx = stepSize
        return dx, dy


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

        if self.switchZ:
            self.values.Fz *= -1
            self.values.Tz *= -1
        """
        log.sensor.debug("Sensor values:")
        log.sensor.debug("Fx: " + str(self.values.Fx) + "N")
        log.sensor.debug("Fy: " + str(self.values.Fy) + "N")
        log.sensor.debug("Fz: " + str(self.values.Fz) + "N")
        log.sensor.debug("Tx: " + str(self.values.Tx) + "Nm")
        log.sensor.debug("Ty: " + str(self.values.Ty) + "Nm")
        log.sensor.debug("Tz: " + str(self.values.Tz) + "Nm")
        """
    
    def zero(self, main = False):
        
        Fx = 0
        Fy = 0
        Fz = 0
        Tx = 0
        Ty = 0
        Tz = 0

        N = 1000
        for _ in range(N):
            self.values = tcp.sensorRead()
            Fx += self.values.Fx
            Fy += self.values.Fy
            Fz += self.values.Fz
            Tx += self.values.Tx
            Ty += self.values.Ty
            Tz += self.values.Tz

        Fx = np.divide(Fx, N)
        Fy = np.divide(Fy, N)
        Fz = np.divide(Fz, N)
        Tx = np.divide(Tx, N)
        Ty = np.divide(Ty, N)
        Tz = np.divide(Tz, N)    
        
        if main:
            self.zeroValuesMain.Fx = Fx
            self.zeroValuesMain.Fy = Fy
            self.zeroValuesMain.Fz = Fz
            self.zeroValuesMain.Tx = Tx
            self.zeroValuesMain.Ty = Ty
            self.zeroValuesMain.Tz = Tz
            '''
            self.zeroValuesMain.Fx = self.values.Fx
            self.zeroValuesMain.Fy = self.values.Fy
            self.zeroValuesMain.Fz = self.values.Fz
            self.zeroValuesMain.Tx = self.values.Tx
            self.zeroValuesMain.Ty = self.values.Ty
            self.zeroValuesMain.Tz = self.values.Tz
            '''
        else:
            self.zeroValues.Fx = Fx
            self.zeroValues.Fy = Fy
            self.zeroValues.Fz = Fz
            self.zeroValues.Tx = Tx
            self.zeroValues.Ty = Ty
            self.zeroValues.Tz = Tz
            '''
            self.zeroValues.Fx = self.values.Fx
            self.zeroValues.Fy = self.values.Fy
            self.zeroValues.Fz = self.values.Fz
            self.zeroValues.Tx = self.values.Tx
            self.zeroValues.Ty = self.values.Ty
            self.zeroValues.Tz = self.values.Tz
            '''

    def transform(self, x, y):
        X = np.array((x,y))
        # X = np.multiply(self.R, X)
        # Changed to
        Xstar = np.dot(self.R, X)
        return float(Xstar[0]),float(Xstar[1])
        
"""
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
"""
