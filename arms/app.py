"""Initialization of arms."""
import arms.config.config as config
import arms.utils.log as log
#from arms.camera.camera import Camera
from time import sleep
from arms.units.abb import ABB
from arms.sensor.sensor import Sensor
from arms.arduino.arduino import Arduino
#from arms.units.alarms import Alarms

import numpy as np
    
class Arms:
	
    """Arms."""
    
    def __init__(self):
        self.sensor = None
        self.records = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0]])
        self.sfp_port_coord = [70.4641, 226.593, -41.8565]
        self.sfp_inserted_coord = [70.804, 225.796, 5.05378]
        
        
    def initialize(self):
        """Initialization routine."""
        # Loggers.
        log.__init__()
        log.log.info("Log file initialized.")
        if config.var.data is None:
            log.config.warning("{}.".format(config.var.error))
        if log.ERROR:
            log.log.warning('Could not find settings in config.')
        
        # Six-axis sensor.
        self.sensor = Sensor()
        self.sensor.connect()
        self.sensor.read()
        sleep(1)
        self.sensor.zero()
        self.sensor.start_ping()

        # Connect to arduino.
        self.arduino = Arduino()
        
        # ABB robot
        self.abb = ABB()
        self.abb.connect()
        # TODO: Return False if an unacceptable error happened,
        # otherwise True.
        return True
    
    def repair(self):

        # 1) Start from the initial position.
        print("-----------------------------------")
        print("1) Start from the initial position.")
        inp = input("Press any key to continue. \n")
        
        x = 125.068
        y = 183.743
        z = -177.026
        q1 = 0.756629
        q2 = 0.0236009
        q3 = -0.00483965
        q4 = -0.6534
        cf1 = 0
        cf4 = -1
        cf6 = -1
        cfx = 0

        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)
        
        # 2) Move in front of the SFP.
        print("-----------------------------------")
        print("2) Move in front of the SFP.")
        inp = input("Press any key to continue. \n")
        
        x = 69.3561
        y = 179.275
        z = -64.891
        q1 = 0.756655
        q2 = 0.0236768
        q3 = -0.00488077
        q4 = -0.653367
        cf1 = 0
        cf4 = -1
        cf6 = -1
        cfx = 0

        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)
        
        # 3) Move to the SFP in gripping position.
        print("-----------------------------------")
        print("3) Move to the SFP in gripping position.")
        inp = input("Press any key to continue. \n")
        
        x = 66.3767
        y = 179.294
        z = 4.10715
        q1 = 0.75665
        q2 = 0.02361
        q3 = -0.00484915
        q4 = -0.653376
        cf1 = -1
        cf4 = -2
        cf6 = -1
        cfx = 0

        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)
        
        # 4) Grip the cable.
        print("-----------------------------------")
        print("4) Grip the cable.")
        inp = input("Press any key to continue. \n")

        self.arduino.close_gripper(4200,300)
        
        ok = False
        while not ok:
            ok = self.arduino.close_gripper(50,300)
        
        # 5) Activate solenoid.
        print("-----------------------------------")
        print("5) Activate solenoid.")
        inp = input("Press any key to continue. \n")
        
        self.arduino.activate_solenoid()
        sleep(1)
        
        # 6) Move back from gripping position.
        print("-----------------------------------")
        print("6) Move back from gripping position.")
        
        z -= 15
        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)

        # 7) Deactivate solenoid.
        print("-----------------------------------")
        print("7) Deactivate solenoid.")
        self.arduino.deactivate_solenoid()

        # 8) Move back even further.
        print("-----------------------------------")
        print("8) Move back even further.")
        inp = input("Press any key to continue. \n")

        z -= 60
        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)


        # 9) Move in front of the helper station.
        print("-----------------------------------")
        print("9) Move in front of the helper station.")
        inp = input("Press any key to continue. \n")
       
        x = 183.541
        y = 221.73
        z = -75
        q1 = 0.756597
        q2 = 0.0234708
        q3 = -0.00477174
        q4 = -0.653443
        cf1 = -1
        cf4 = -2
        cf6 = 0
        cfx = 0
        
        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)

        # 10) Move in front of the new SFP.
        print("-----------------------------------")
        print("10) Move in front of the new SFP.")
        inp = input("Press any key to continue. \n")

        x = 185.371
        y = 221.704
        z = -7.00289
        q1 = 0.75652
        q2 = 0.023267
        q3 = -0.00485096
        q4 = -0.653538
        cf1 = -1
        cf4 = -2
        cf6 = 0
        cfx = 0
        
        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)


        # 11) Move into new SFP.
        print("-----------------------------------")
        print("11) Move into new SFP.")
        inp = input("Press any key to continue. \n")
    
        z += 9.3169
        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)

        # 12) Move in front of the helper station.
        print("-----------------------------------")
        print("12) Move in front of the helper station.")
        inp = input("Press any key to continue. \n")
    
        z -= 85
        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)

    
        # 13) Move again in front of the SFP port.
        print("-----------------------------------")
        print("13) Move again in front of the SFP port.")
        inp = input("Press any key to continue. \n")
        
        delta_x = 2.0*0
        delta_y = 4.0*0
        x = round(70.4641 + delta_x, 4)
        y = round(226.593 + delta_y, 3)
        z = round(-41.8565 - 10.0, 4)
        q1 = 0.756421
        q2 = 0.0228897
        q3 = -0.00476848
        q4 = -0.653667
        cf1 = -1
        cf4 = -2
        cf6 = -1
        cfx = 0

        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)
        self.sensor.zero()
        
        # 14) Find hole.
        print("-----------------------------------")
        print("14) Find hole.")
        inp = input("Press any key to continue. \n")
        self.find_hole(0, 0, 4)

    
        # 15) Insert SFP.
        print("-----------------------------------")
        print("15) Insert SFP.")
        inp = input("Press any key to continue. \n")
        ok = self.insert(0, 0, 0)
        if not ok:
            return

        # 16) Release Gripper.
        print("-----------------------------------")
        print("16) Release Gripper.")
        inp = input("Press any key to continue. \n")
        self.arduino.open_gripper(4000,10)
        #if not ok:
        #   return

        # 17) Move back a little.
        print("-----------------------------------")
        print("17) Move back a little")
        inp = input("Press any key to continue. \n")
        #self.arduino.open_gripper(4000,0)
        ok = self.abb.delta_move(0, 0, -50)
        
        x = 125.068
        y = 183.743
        z = -177.026
        q1 = 0.756629
        q2 = 0.0236009
        q3 = -0.00483965
        q4 = -0.6534
        cf1 = 0
        cf4 = -1
        cf6 = -1
        cfx = 0

        ok = self.abb.move(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx)
        #if not ok:
        #   return

        # Done.
        print("-----------------------------------")
        print("Done")


    def find_hole(self, dx, dy, dz):

        print("-----------------------------------")
        #if dz == -1.5:
         #   inp = input("Press any key to continue. \n")

        # Make a relative movement.
        self.abb.delta_move(0, 0, dz)
        self.abb.delta_move(dx, dy, 0)

        # Reset
        dx = 0
        dy = 0
        dz = 0
        
        # Make adjustments.
        self.record()
        adx, ady = self.adjustment()
        if [adx, ady] == [0, 0]:
            # Go further in z-direction.
            print("Go further in z-direction.")
            dz = 0.1
        else:
            # Step out in z-direction.
            print("Step out in z-direction.")
            dx = adx
            dy = ady
            dz = -1.5

        # Check drop.
        ok, data = self.abb.get_position()
        x = data[0]
        y = data[1]
        z = data[2]
        print("Current position (x, y, z): ({}, {}, {})".format(x, y, z))
        
        sfp_port_z = self.sfp_port_coord[2]
        if z > sfp_port_z:
            print("Found hole")
            return
        else:
            print("Retry.")
            return self.find_hole(dx, dy, dz)
        
        
    def adjustment(self):

        # Initial values.
        threshold_Fz = 10.0
        threshold_Tx = 0.07
        threshold_Ty = 0.05
        
        dx = 0
        dy = 0

        step = 0.5
        
        # Read forces and torques.
        self.sensor.read()
        Fx = self.sensor.values.Fx
        Fy = self.sensor.values.Fy
        Fz = self.sensor.values.Fz
        Tx = self.sensor.values.Tx
        Ty = self.sensor.values.Ty
        Tz = self.sensor.values.Tz

        print("Forces: (Fx, Fy, Fz) = ({}, {}, {})".format(Fx, Fy, Fz))
        print("Torques: (Tx, Ty, Tz) = ({}, {}, {})".format(Tx, Ty, Tz))
        
        if Fz >= threshold_Fz:
            if abs(Ty) >= threshold_Ty:
                if Ty > 0:
                    dx = step
                else:
                    dx = -step
                print("Adjusting dx = {}".format(dx))
            elif abs(Tx) >= threshold_Tx:
                if Tx > 0:
                    dy = -step
                else:
                    dy = step
                print("Adjusting dy = {}".format(dy))
			                         
        return dx, dy

    def insert(self, dx, dy, dz, stop=False):
        print("-----------------------------------")
        if stop is True:

            return False
        
        #if dz == 0.0:
        #   inp = input("Press any key to continue. \n")

        # Make a relative movement.
        self.abb.delta_move(0, 0, dz)
        self.abb.delta_move(dx, dy, 0)

        # Reset
        dx = 0
        dy = 0
        dz = 0
        
        # Make adjustments.
        self.record()
        adx, ady, stop = self.adjustment_hole()
        if [adx, ady] == [0, 0]:
            # Go further in z-direction.
            print("Go further in z-direction.")
            dz = 0.5
        else:
            # Step out in z-direction.
            print("Step out in z-direction.")
            dx = adx
            dy = ady
            dz = 0.0

        # Check drop.
        ok, data = self.abb.get_position()
        x = data[0]
        y = data[1]
        z = data[2]
        print("Current position (x, y, z): ({}, {}, {})".format(x, y, z))
        
        sfp_port_z = self.sfp_inserted_coord[2]
        if z > sfp_port_z:
            print("Fully inserted.")
            return True
        else:
            print("Retry.")
            return self.insert(dx, dy, dz, stop)

        
    def adjustment_hole(self):
        # Initial values.
        threshold_Fz = 30.0
        threshold_Fx = 5.0
        threshold_Fy = 5.0
        
        dx = 0
        dy = 0

        step = 0.1
        
        # Read forces and torques.
        self.sensor.read()
        Fx = self.sensor.values.Fx
        Fy = self.sensor.values.Fy
        Fz = self.sensor.values.Fz
        Tx = self.sensor.values.Tx
        Ty = self.sensor.values.Ty
        Tz = self.sensor.values.Tz

        print("Forces: (Fx, Fy, Fz) = ({}, {}, {})".format(Fx, Fy, Fz))
        print("Torques: (Tx, Ty, Tz) = ({}, {}, {})".format(Tx, Ty, Tz))
        
        if Fz < threshold_Fz:
            if abs(Fy) >= threshold_Fy:
                if Fy > 0:
                    dy = step
                else:
                    dy = -step
                print("Adjusting dx = {}".format(dx))
            elif abs(Fx) >= threshold_Fx:
                if Fx > 0:
                    dx = step
                else:
                    dx = -step
                print("Adjusting dy = {}".format(dy))
            return dx, dy, False
        else:
            print("Fz reached the threshold. Manually action needed.")
            return dx, dy, True        
        
        
    def record(self):

        # Coordinates.
        ok, data = self.abb.get_position()

        x = data[0]
        y = data[1]
        z = data[2]

        # Forces and Torques.
        self.sensor.read()
        Fx = round(self.sensor.values.Fx, 5)
        Fy = round(self.sensor.values.Fy, 5)
        Fz = round(self.sensor.values.Fz, 5)
        Tx = round(self.sensor.values.Tx, 5)
        Ty = round(self.sensor.values.Ty, 5)
        Tz = round(self.sensor.values.Tz, 5)
           
        # Save changes to file.
        if self.records.shape[0] < 800:
            self.records = np.concatenate((self.records, np.array([[x, y, z, Fx, Fy, Fz, Tx, Ty, Tz]])), axis=0)
            np.savetxt("records.csv", self.records, delimiter=",")
        else:
            self.records = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0]])
            self.records = np.concatenate((self.records, np.array([[x, y, z, Fx, Fy, Fz, Tx, Ty, Tz]])), axis=0)
            np.savetxt("records2.csv", self.records, delimiter=",")

    def record_foto(self):
        print("record")
        # Coordinates.
        x = 0
        y = 0
        z = 0

        # Forces and Torques.
        self.sensor.read()
        Fx = round(self.sensor.values.Fx, 5)
        Fy = round(self.sensor.values.Fy, 5)
        Fz = round(self.sensor.values.Fz, 5)
        Tx = round(self.sensor.values.Tx, 5)
        Ty = round(self.sensor.values.Ty, 5)
        Tz = round(self.sensor.values.Tz, 5)
            
        # Save changes to file.
        self.records = np.concatenate((self.records, np.array([[x, y, z, Fx, Fy, Fz, Tx, Ty, Tz]])), axis=0)
        
        np.savetxt("records.csv", self.records, delimiter=",")

        sleep(0.3)
        return self.record_foto()
        
def main():
    """Initialize and start Arms."""
    arms = Arms()
    if arms.initialize():
        try:
            arms.repair()
            #arms.record_foto()
        except KeyboardInterrupt:
            arms.abb.close()
            arms.arduino.disconnect()
            arms.sensor.stop_ping()
            arms.sensor.disconnect()
            
def main2():
    """Main routine."""
    #initialization()
    a = Arduino()
    abb = ABB()
    abb.connect()
    sensor = Sensor()
    sensor.connect()
    sensor.read()
    sleep(1)
    sensor.zero()
    sensor.start_ping()
        
    while True:
        try:
            print("-----------------------------------------")
            inp = input("Press a number to control arduino. \n")
            try:
                if int(inp) == 1:
                    a.close_gripper(1000,300)
                elif int(inp) == 2:
                    a.close_gripper(200,300)    
                elif int(inp) == 3:
                    a.acknowledge_error()
                    a.open_gripper(2000,30)
                elif int(inp) == 4:
                    a.activate_solenoid()
                    sleep(1)
                    a.deactivate_solenoid()
                elif int(inp) == 5:
                    a.request_info()
                elif int(inp) == 6:
                    ok, data = abb.get_position()
                    print(data)
                elif int(inp) == 7:
                    # Forces and Torques.
                    sensor.read()
                    Fx = round(sensor.values.Fx, 5)
                    Fy = round(sensor.values.Fy, 5)
                    Fz = round(sensor.values.Fz, 5)
                    Tx = round(sensor.values.Tx, 5)
                    Ty = round(sensor.values.Ty, 5)
                    Tz = round(sensor.values.Tz, 5)
                    print("Forces: (Fx, Fy, Fz) = ({}, {}, {})".format(Fx, Fy, Fz))
                    print("Torques: (Tx, Ty, Tz) = ({}, {}, {})".format(Tx, Ty, Tz))
            except:
                pass
            
      
        except KeyboardInterrupt:
            a.disconnect()
            abb.close()
    
    #arms = ARMS()
    #arms.test_sensor()
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(17, GPIO.OUT)

    #while True:
     #   GPIO.output(17, GPIO.HIGH)
      #  sleep(15/(130*2))
       # GPIO.output(17, GPIO.LOW)
        #sleep(45/(130*2))
    #c = Camera(True)
    #c.evaluate(True)
    #c.evaluate(True,'2018-11-26 15:56:09.641098')
    #c.cableInsertion(True,'2018-11-26 15:02:42.568639')
    #a = np.array(([1],[2]))
    #
    #print(a.shape)



    
