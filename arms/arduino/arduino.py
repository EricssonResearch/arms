
import arms.utils.log as log
class Arduino:
    def __init__(self):
        self.currentClawDist = 0.0
        """
        Calculate the amount of pulses needed to reach a certain gripper width (measured from the edge if the
        pinchers). Saves the new position as current after execution
        Input:
        new - desired width
        
        Output:
        pulses - amount of pulses to reach the width
        CW - clockwise = True, Counter-clockwise = False
        """
    def getTranslation(self, new):
        if new > 38.42 or new < 0.0:
            log.ard_log.warning("Invalid distance from " + str(self.currentClawDist) + " to " + str(new))
            raise ValueError("Invalid distance.")
        dist = self.currentClawDist + new
        dist2 = dist*13.24/38.42
        revs = dist2/0.5
        pulses = int(revs*200)
        log.ard_log.debug("Moving from " + str(self.currentClawDist) + " to " + str(new))
        self.currentClawDist -= float(pulses)/400*38.42/13.24
        log.ard_log.debug("Actual distance reached: " + str(self.currentClawDist))
        log.ard_log.debug("Pulses: " + str(abs(pulses)) + ", Clockwise: " + str(dist >= 0))
        return abs(pulses), (dist >= 0)
