#!/usr/bin/env python

# HOW WE DO IT IN RTCADS

import re


class BadAlarmFile(Exception):
    pass


class VarItem(object):
    def _setAlarms (self):
        """Select and load an alarm file and provide alarm file display item.
        """
        # Guess which alarm file to use.
        # Determine active side of HRC.
        if (VarItem.data_dict ['S_BusSelImgHvps'][1] == 0
            and VarItem.data_dict ['S_BusSelSpecHvps'][1] == 0):
            # Side A electronics are active
            if VarItem.data_dict ['S_DetSelPreampA'][1] == 0:
                if VarItem.data_dict ['EdgeBlkValidityEnable'][1]:
                    alarmFileName = 'HRC-I-TRIM.alarm'
                else:
                    alarmFileName = 'HRC-I.alarm'
            elif VarItem.data_dict ['S_InstSelect'][1] == 1:
                alarmFileName = 'HRC-S.alarm'
            else:
                alarmFileName = 'HRC-S-IMG.alarm'
        else:
            # Side B electronics are active
            if VarItem.data_dict ['S_DetSelPreampB'][1] == 0:
                if VarItem.data_dict ['EdgeBlkValidityEnable'][1]:
                    alarmFileName = 'HRC-I-TRIM-B.alarm'
                else:
                    alarmFileName = 'HRC-I-B.alarm'
            elif VarItem.data_dict ['S_InstSelect'][1] == 1:
                alarmFileName = 'HRC-S-B.alarm'
            else:
                alarmFileName = 'HRC-S-IMG-B.alarm'

        # Read the alarm file only if it has changed
        if alarmFileName != VarItem.alarmFileName:
            alarmFilePath = '/d0/hrc/rtcads/ALARMS'
            VarItem.alarmSet = readAlarmFile (alarmFilePath, alarmFileName)
            VarItem.alarmFileName = alarmFileName
        self.state = 'off'
        self.value = alarmFileName

    def _alarmState (self, conval):
        """Determine alarm state - general case.
        """
        self.state = 'off'
        alarms = VarItem.alarmSet [self.varname]
        if alarms ['status']:
            if conval <= alarms ['rll'] or conval >= alarms ['rul']:
                self.state = 'bad'
            elif conval <= alarms ['yll'] or conval >= alarms ['yul']:
                self.state = 'warn'
            else:
                self.state = 'good'



def readAlarmFile(path, fname):
    """Alarm limits are stored in a dictionary indexed by variable name.
    """
    alarm_file = path + '/' + fname
    with open(alarm_file) as afh:
        alarm_dict = dict()
        for line in afh:
            if not re.match(r'#', line):
                pcs = re.split('\t', line)
                if len(pcs) == 6:
                    alarm_dict[pcs[0]] = dict([('status', int(pcs[1])),
                                        ('rll', float(pcs[2])), # Red lower limit
                                        ('yll', float(pcs[3])), # Yellow Limit Low
                                        ('yul', float(pcs[4])), # Yellow Limit High
                                        ('rul', float(pcs[5]))]) # Red upper limit =
                else:
                    raise BadAlarmFile(alarm_file)
        return alarm_dict
