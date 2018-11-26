
import arms.sensor.tcp as tcp
import sys
import arms.utils.log as log

"""
A simple implementation with an initialization that can take a different ip adress
if necessary.
The connect method connects and the disconnect method disconnects
the read method saves all the sensor values to the sensor.values attribute.
To access the values you type sensor.values.Fx or .Ty etc.
"""

class Sensor:
    def __init__(self, ip = "192.168.1.1"):
        self.values = None
        self.ip = ip
        
    def connect(self):    
        tcp.sensorConnect(self.ip)
        log.sensor.info("Sensor connected at address:" + self.ip)
        
    def disconnect(self):
        tcp.sensorDisconnect()
        log.sensor.info("Sensor disconnected from address:" + self.ip)

    def read(self):
        self.values = tcp.sensorRead()
        log.sensor.debug("Sensor values:")
        log.sensor.debug("Fx: " + str(self.values.Fx) + "N")
        log.sensor.debug("Fy: " + str(self.values.Fy) + "N")
        log.sensor.debug("Fz: " + str(self.values.Fz) + "N")
        log.sensor.debug("Tx: " + str(self.values.Tx) + "Nm")
        log.sensor.debug("Ty: " + str(self.values.Ty) + "Nm")
        log.sensor.debug("Tz: " + str(self.values.Tz) + "Nm")
        

def main():
    #sys.path("/home")
    #sys.argv = ['build_ext', '--inplace']
    #exec('setup.py')
    tcp.sensorConnect("192.168.1.1")
    for i in range(10):
        r = tcp.sensorRead()
        print(r.Fx)
        print(r.Fy)
        print(r.Fz)
        print(r.Tx)
        print(r.Ty)
        print(r.Tz)
        time.sleep(1)
    tcp.sensorDisconnect()

if __name__ == "__main__":
    main()
