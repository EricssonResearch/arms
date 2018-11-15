
import arms.utils.log as log
class Arduino:
    def __init__(self):
        self.currentActStroke = 0.0
        self.currentClawDist = 79.00
        self.clawDict = {}
        file = open("arms/arduino/gripperPos.txt", "r")
        fileString = file.read().split("\n")
        for row in fileString:
            values = row.split(":")
            if values[0] in self.clawDict:
                values[1] = (self.clawDict[float(values[0])] + float(values[1]))/2
                self.clawDict[float(values[0])] = values[1]
            else:
                self.clawDict[float(values[0])] = float(values[1])
        """
        Calculate the amount of pulses needed to reach a certain gripper width (measured from the edge if the
        pinchers). Saves the new position as current after execution
        Input:
        new - desired width with format xx.xx
        
        Output:
        pulses - amount of pulses to reach the width
        CW - clockwise = True, Counter-clockwise = False
        """
    def getTranslation(self, new):
        if new not in self.clawDict:
            log.ard_log.warning("Invalid distance from " + str(self.currentClawDist) + " to " + str(new))
            raise ValueError("Invalid distance.")
        #dist = self.currentClawDist + new
        #dist2 = dist*13.24/38.42
        dist = self.clawDict[new] - self.currentActStroke
        revs = dist/0.5
        pulses = int(revs*200)
        log.ard_log.debug("Moving from " + str(self.currentClawDist) + " to " + str(new))
        self.currentActStroke = self.clawDict[new]
        self.currentClawDist = new
        log.ard_log.debug("Pulses: " + str(abs(pulses)) + ", Clockwise: " + str(dist >= 0))
        return abs(pulses), (dist >= 0)
