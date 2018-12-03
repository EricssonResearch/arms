"""Initialization of arms."""

from arms.config import config
from arms.utils import log
from arms.uart.Arduino_RPI_communication_new import Arduino
import time
from arms.Camera import Camera
#from arms.units import ABB

def main():
    """Main routine."""
    initialization()

#--------------------------------------INITIALIZATION-------------------------------------
def initialization():
    """Initialization routine."""
    log.__init__()
    log.log.info("Log file initialized.")
    if config.var.data is None:
        log.config.warning("{}.".format(config.var.error))
    if log.ERROR:
        log.log.warning('Could not find settings in config.')
    
    
    '''
    while(1):
        try:
            a.send("1,3,1.0;2;3.14;")
            time.sleep(0.5)
            a.send("2,3,4.0;2;3.14;")
            time.sleep(0.5)
        except KeyboardInterrupt:
            a.disconnect()
            break
    print(a.ID +' '+a.fields+' '+str(a.data))
    '''
    
    #Initialize the Arduino class and calibrate gripper
    Ard = Arduino()
    Ard.calibrate_gripper()
    Ard.disconnect()
    
    
    #Initialize the camera classs
    piCam = Camera()
    
    #Initialize the robotic arm
    '''
    maybe this step should be in the repair cycle?
    '''
    Robot = ABB()
    
    #Initialize 6-axis sensor
    6axis = Sensor()
    6axis.zero(True)
    
    print("printing in app.py - final line")

def read_error_message_from_DU():
    #this function listens to the port to see if there is any error message,
    #then it interprets this and gives us the coordinates for the broken SFP
    broken_SFP = message_content(error_message)


#-------------------------------------------REPAIR CYCLE---------------------------------    
def repair_cycle():
    '''
    An error message from the DU has been received and properly decoded,
    so we know which port needs to be changed
    When entering the repair cycle, positions broken_SFP and new_SFP are known
    '''
    app.info("Starting repair cycle")
    
    #establish connection to relevant parts
    Ard.connect()
    
    '''
    depending if we initialize the robot in this step or not,
    couldn't see a "connect" command but leaving it here to give the gist of it
    '''
    Robot.connect()
    app.debug("Established connections")
    
    '''
    move command needs to be altered depending on whether we hold NOTHING, CABLE,
    or CABLE + SFP, since the length of the tool varies accordingly
    '''
    holding_cable = False
    holding_cable_and_SFP = False
    take_picture = False #no CV for grabbing cable at broken SFP
    cable_and_SFP_inserted = True  #if the target has SFP and cable inserted
    SFP_inserted = False #if the target position has only SFP inserted
    
    Robot.move(broken_SFP)
    app.debug("Gripper positioned at " + broken_SFP)
    
    #Close the gripper around cable in the broken SFP and extract it
    Ard.close_gripper(6000,400)
    if (Ard.pressure_error or Ard.obstacle_error):
        app.error("Error received")
        return
    app.debug("Closed Gripper around cable")
    Ard.activate_solenoid()
    #we can maybe implement the current sensor on the solenoid circuit here to see if it is active or not.
    #we could also implement a timer that automatically shuts off solenoid so it's not on for too long as it can start to burn
    if(not Ard.solenoid_active):
        app.error("Solenoid never activated")
        return
    app.debug("Solenoid engaged")
    Robot.delta_move(Z = Z + 50 mm) #move the robotic arm out around 50 mm to extract cable
    app.debug("Extracted cable")
    Ard.deactivate_solenoid()
    if(Ard.solenoid_active):
        app.error("Solenoid never deactivated")
        return
    app.debug("Solenoid Disengaged")
    
    app.info("Cable extracted from broken SFP")
    
    #Move the cable to the new SFP and insert it
    holding_cable = True #introduces an offset for when holding a cable
    holding_cable_and_SFP = False
    take_picture = False #we want to use CV to make sure we are positioned correctly at new SFP, this variable introduces an offset to the saved position
    cable_and_SFP_inserted = False  #if the target has SFP and cable inserted
    SFP_inserted = True #if the target position has only SFP inserted
    
    Robot.move(new_SFP + cable_offset + camera_offset)
    app.debug("Moved gripper towards new SFP position, so a picture can be taken")
    
    #Allow the picam to take picture and evaluate it
    CORRECT_POSITION = False #we assume that our positioning is not completely correct, this flag/variable needs to be set to true inthe piCam class
    
    #keep taking pictures and adjusting until the position is correct
    while(CORRECT_POSITION == False)
        [delta_x, delta_y, delta_z, delta_wristAngle] = piCam.evaluate()
        #adjust robot position properly
        Robot.delta_move(delta_x, delta_y, delta_z, delta_wristAngle)
    
    #get back in position for inserting cable into new SFP
    Robot.delta_move( -camera_offset)
    
    #insert the cable, open gripper and mvoe robot outside a litte
    Robot.insert_cable()
    app.debug("Cable inserted")
    Ard.open_gripper(Ard.pulses,0)
    if (Ard.pressure_error or Ard.obstacle_error):
        app.error("Error received")
        return
    app.debug("Gripper opened")
    Robot.delta_move(Z = Z + 50 mm)
    
    app.info("Cable inserted into new SFP")
    
    
    #Move back to the broken SFP in order to extract it from the DU
    holding_cable = False #introduces an offset for when holding a cable
    holding_cable_and_SFP = False
    take_picture = False #We could maybe use CV here to detect the naked SFP in the DU
    cable_and_SFP_inserted = False  #if the target has SFP and cable inserted
    SFP_inserted = True #if the target position has only SFP inserted
    
    Robot.move(broken_SFP)
    Robot.extract_SFP()
    app.info("Broken SFP removed")
    
    #Go back to new SFP + cable assembly and pick it up
    holding_cable = False #introduces an offset for when holding a cable
    holding_cable_and_SFP = False
    take_picture = False #We could maybe use CV here to detect the naked SFP in the DU
    cable_and_SFP_inserted = True  #if the target has SFP and cable inserted
    SFP_inserted = False #if the target position has only SFP inserted
    
    Robot.move(new_SFP)
    Ard.close_gripper(6000,400)
    if (Ard.pressure_error or Ard.obstacle_error):
        app.error("Error received")
        return
    Robot.delta_move(cable_and_SFP_assembly_offset)
    app.info("New SFP with cable picked up")
    
    
    #Take the assembly back to the DU port where the broken SFP was and insert it
    holding_cable = False #introduces an offset for when holding a cable
    holding_cable_and_SFP = True
    take_picture = False #We could maybe use CV here to detect the naked SFP in the DU
    cable_and_SFP_inserted = False  #if the target has SFP and cable inserted
    SFP_inserted = False #if the target position has only SFP inserted
    
    Robot.move(broken_SFP)
    Robot.insert_SFP()
    Ard.open_gripper(Ard.pulses,0)
    if (Ard.pressure_error or Ard.obstacle_error):
        app.error("Error received")
        return
    Robot.delta_move(cable_and_SFP_inserted_offset)
    app.info("New SFP inserted into port")
    
    #move the robot into standby position and power things down
    Robot.move(standby_position)
    Ard.disconnect()
    Robot.disconnect()
    app.info("Robot back in standby position, powering down")
    
    return
        
    
    
    
    
    
    